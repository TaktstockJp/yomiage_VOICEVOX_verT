"""利用者ごとの声、調声、単語帳、設定を SQLite に保存する。"""

from __future__ import annotations

import sqlite3
from dataclasses import asdict, dataclass, replace
from pathlib import Path

from .tts.base import VoiceSelection

_SCHEMA = """
CREATE TABLE IF NOT EXISTS user_voices (
    user_id INTEGER PRIMARY KEY,
    engine  TEXT NOT NULL,
    speaker TEXT NOT NULL,
    style   TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS style_params (
    engine  TEXT NOT NULL,
    speaker TEXT NOT NULL,
    style   TEXT NOT NULL,
    param   TEXT NOT NULL,
    value   REAL NOT NULL,
    PRIMARY KEY (engine, speaker, style, param)
);
CREATE TABLE IF NOT EXISTS dictionary (
    word    TEXT PRIMARY KEY,
    reading TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS settings (
    key   TEXT PRIMARY KEY,
    value INTEGER NOT NULL
);
"""


@dataclass(frozen=True)
class Settings:
    notify_join_leave: bool = True
    report_member_count: bool = True
    auto_leave: bool = True
    time_signal: bool = True
    max_chars: int = 50


class Storage:
    """SQLite データベースへの読み書きをまとめたクラス。Bot のイベントループ上でだけ使う。"""

    def __init__(self, path: Path | str) -> None:
        self._connection = sqlite3.connect(path)
        with self._connection:
            self._connection.executescript(_SCHEMA)

    def close(self) -> None:
        self._connection.close()

    def user_voice(self, user_id: int) -> VoiceSelection | None:
        row = self._connection.execute(
            "SELECT engine, speaker, style FROM user_voices WHERE user_id = ?",
            (user_id,),
        ).fetchone()
        return VoiceSelection(*row) if row else None

    def set_user_voice(self, user_id: int, voice: VoiceSelection) -> None:
        with self._connection:
            self._connection.execute(
                "INSERT OR REPLACE INTO user_voices (user_id, engine, speaker, style) VALUES (?, ?, ?, ?)",
                (user_id, voice.engine, voice.speaker, voice.style),
            )

    def style_params(self, voice: VoiceSelection) -> dict[str, float]:
        rows = self._connection.execute(
            "SELECT param, value FROM style_params WHERE engine = ? AND speaker = ? AND style = ?",
            (voice.engine, voice.speaker, voice.style),
        )
        return dict(rows.fetchall())

    def set_style_param(self, voice: VoiceSelection, param: str, value: float) -> None:
        with self._connection:
            self._connection.execute(
                "INSERT OR REPLACE INTO style_params (engine, speaker, style, param, value) "
                "VALUES (?, ?, ?, ?, ?)",
                (voice.engine, voice.speaker, voice.style, param, value),
            )

    def delete_style_param(self, voice: VoiceSelection, param: str) -> None:
        """初期値に戻すときに呼ぶ。保存するのは初期値から変更した値だけにする。"""
        with self._connection:
            self._connection.execute(
                "DELETE FROM style_params WHERE engine = ? AND speaker = ? AND style = ? AND param = ?",
                (voice.engine, voice.speaker, voice.style, param),
            )

    def words(self) -> list[tuple[str, str]]:
        """単語帳を、長い単語から順に返す。"""
        rows = self._connection.execute(
            "SELECT word, reading FROM dictionary ORDER BY length(word) DESC, word"
        )
        return rows.fetchall()

    def set_word(self, word: str, reading: str) -> None:
        with self._connection:
            self._connection.execute(
                "INSERT OR REPLACE INTO dictionary (word, reading) VALUES (?, ?)",
                (word, reading),
            )

    def delete_word(self, word: str) -> bool:
        """単語を削除する。登録されていなければ False を返す。"""
        with self._connection:
            cursor = self._connection.execute("DELETE FROM dictionary WHERE word = ?", (word,))
        return cursor.rowcount > 0

    def settings(self) -> Settings:
        defaults = Settings()
        rows = dict(self._connection.execute("SELECT key, value FROM settings").fetchall())
        stored = {
            key: type(default)(rows[key])
            for key, default in asdict(defaults).items()
            if key in rows
        }
        return replace(defaults, **stored)

    def set_setting(self, key: str, value: bool | int) -> None:
        if key not in asdict(Settings()):
            raise KeyError(key)
        with self._connection:
            self._connection.execute(
                "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
                (key, int(value)),
            )
