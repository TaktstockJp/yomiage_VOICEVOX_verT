"""利用できる TTS エンジンの登録と、声の検索。"""

from __future__ import annotations

import logging
from collections.abc import Sequence

from .base import TTSEngine, VoiceNotFoundError, VoiceSelection

_log = logging.getLogger(__name__)


class EngineRegistry:
    def __init__(self) -> None:
        self._engines: dict[str, TTSEngine] = {}

    def engines(self) -> Sequence[TTSEngine]:
        return tuple(self._engines.values())

    def get(self, name: str) -> TTSEngine | None:
        return self._engines.get(name)

    async def add(self, engine: TTSEngine) -> bool:
        """エンジンを起動して登録する。起動に失敗したら登録せずに False を返す。"""
        if engine.name in self._engines:
            raise ValueError(f"エンジン名が重複しています: {engine.name}")
        try:
            await engine.start()
        except Exception as error:
            _log.warning("%s を起動できないため、利用しません: %s", engine.name, error)
            await self._close(engine)
            return False
        if not engine.speakers():
            _log.warning("%s に利用できる話者がいないため、利用しません", engine.name)
            await self._close(engine)
            return False
        self._engines[engine.name] = engine
        _log.info("%s を登録しました（話者 %d 名）", engine.name, len(engine.speakers()))
        return True

    def find(self, speaker: str, style: str, engine: str | None = None) -> VoiceSelection | None:
        """話者とスタイルが一致する声を探す。engine を省略すると登録順に全エンジンを探す。"""
        candidates = self.engines() if engine is None else [self._engines.get(engine)]
        for candidate in candidates:
            if candidate is not None and candidate.has_voice(speaker, style):
                return VoiceSelection(candidate.name, speaker, style)
        return None

    def resolve(self, *preferred: VoiceSelection | None) -> VoiceSelection:
        """利用できる最初の声を返す。どれも使えなければ最初のエンジンの最初の声を返す。"""
        for voice in preferred:
            if voice is not None and self.find(voice.speaker, voice.style, voice.engine):
                return voice
        for engine in self.engines():
            speaker = engine.speakers()[0]
            return VoiceSelection(engine.name, speaker.name, speaker.styles[0].name)
        raise VoiceNotFoundError("利用できるエンジンがありません")

    async def reload_all(self) -> list[str]:
        """全エンジンの話者一覧を取り直し、失敗したエンジンの名前を返す。"""
        failed: list[str] = []
        for engine in self.engines():
            try:
                await engine.reload()
            except Exception as error:
                _log.warning("%s の話者一覧を更新できませんでした: %s", engine.name, error)
                failed.append(engine.name)
        return failed

    async def close_all(self) -> None:
        for engine in self.engines():
            await self._close(engine)
        self._engines.clear()

    @staticmethod
    async def _close(engine: TTSEngine) -> None:
        try:
            await engine.close()
        except Exception:
            _log.exception("%s の終了処理に失敗しました", engine.name)
