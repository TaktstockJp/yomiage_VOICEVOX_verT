"""config.toml を型付きの dataclass に読み込む。"""

from __future__ import annotations

import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, TypeVar


class ConfigError(Exception):
    """設定ファイルに問題があることを、利用者向けの日本語メッセージで伝える例外。"""


@dataclass(frozen=True)
class DiscordConfig:
    token: str = field(repr=False)
    command_prefix: str = "!"
    comment_prefix: str = ">"
    ignore_prefixes: tuple[str, ...] = ("$", "?")


@dataclass(frozen=True)
class DefaultVoiceConfig:
    engine: str = "VOICEVOX"
    speaker: str = "ずんだもん"
    style: str = "あまあま"


@dataclass(frozen=True)
class FfmpegConfig:
    path: str = ""


@dataclass(frozen=True)
class VoicevoxEngineConfig:
    name: str
    port: int


@dataclass(frozen=True)
class CoeiroinkConfig:
    enabled: bool = False
    port: int = 50032


@dataclass(frozen=True)
class AiVoiceConfig:
    enabled: bool = False
    dir: Path = Path(r"C:\Program Files\AI\AIVoice\AIVoiceEditor")


@dataclass(frozen=True)
class VoicepeakConfig:
    enabled: bool = False
    exe: Path = Path(r"C:\Program Files\VOICEPEAK\voicepeak.exe")


@dataclass(frozen=True)
class VoisonaConfig:
    enabled: bool = False
    port: int = 32766
    user: str = field(default="", repr=False)
    password: str = field(default="", repr=False)


@dataclass(frozen=True)
class EnginesConfig:
    voicevox: tuple[VoicevoxEngineConfig, ...] = ()
    coeiroink: CoeiroinkConfig = CoeiroinkConfig()
    aivoice: AiVoiceConfig = AiVoiceConfig()
    voicepeak: VoicepeakConfig = VoicepeakConfig()
    voisona: VoisonaConfig = VoisonaConfig()


@dataclass(frozen=True)
class Config:
    discord: DiscordConfig
    default_voice: DefaultVoiceConfig
    ffmpeg: FfmpegConfig
    engines: EnginesConfig


T = TypeVar("T")
_REQUIRED: Any = object()


def _value(table: dict[str, Any], key: str, expected: type[T], section: str, default: T = _REQUIRED) -> T:
    if key not in table:
        if default is _REQUIRED:
            raise ConfigError(f"設定ファイルの [{section}] に {key} がありません。")
        return default
    value = table[key]
    # bool は int のサブクラスなので、isinstance では true を数値として通してしまう
    if type(value) is not expected:
        raise ConfigError(f"設定ファイルの [{section}] の {key} の値の形式が正しくありません。")
    return value


def _table(parent: dict[str, Any], key: str, section: str) -> dict[str, Any]:
    return _value(parent, key, dict, section, {})


def _text(table: dict[str, Any], key: str, section: str, default: str = _REQUIRED) -> str:
    value = _value(table, key, str, section, default)
    if not value:
        raise ConfigError(f"設定ファイルの [{section}] の {key} が空です。")
    return value


def _port(table: dict[str, Any], section: str, default: int = _REQUIRED) -> int:
    port = _value(table, "port", int, section, default)
    if not 1 <= port <= 65535:
        raise ConfigError(f"設定ファイルの [{section}] の port は 1〜65535 で指定してください。")
    return port


def _parse_discord(data: dict[str, Any]) -> DiscordConfig:
    section = "discord"
    table = _table(data, section, section)
    prefixes = _value(table, "ignore_prefixes", list, section, ["$", "?"])
    if not all(isinstance(prefix, str) and prefix for prefix in prefixes):
        raise ConfigError("設定ファイルの [discord] の ignore_prefixes は空でない文字列の配列にしてください。")
    return DiscordConfig(
        token=_text(table, "token", section),
        command_prefix=_text(table, "command_prefix", section, "!"),
        comment_prefix=_text(table, "comment_prefix", section, ">"),
        ignore_prefixes=tuple(prefixes),
    )


def _parse_default_voice(data: dict[str, Any]) -> DefaultVoiceConfig:
    section = "default_voice"
    table = _table(data, section, section)
    defaults = DefaultVoiceConfig()
    return DefaultVoiceConfig(
        engine=_text(table, "engine", section, defaults.engine),
        speaker=_text(table, "speaker", section, defaults.speaker),
        style=_text(table, "style", section, defaults.style),
    )


def _parse_voicevox(engines: dict[str, Any]) -> tuple[VoicevoxEngineConfig, ...]:
    section = "engines.voicevox"
    items = _value(engines, "voicevox", list, "engines", [])
    parsed: list[VoicevoxEngineConfig] = []
    for item in items:
        if not isinstance(item, dict):
            raise ConfigError("設定ファイルの engines.voicevox は [[engines.voicevox]] の形で書いてください。")
        parsed.append(VoicevoxEngineConfig(name=_text(item, "name", section), port=_port(item, section)))
    names = [engine.name for engine in parsed]
    if len(set(names)) != len(names):
        raise ConfigError("設定ファイルの engines.voicevox に同じ name が複数あります。")
    return tuple(parsed)


def _parse_voisona(engines: dict[str, Any]) -> VoisonaConfig:
    section = "engines.voisona"
    table = _table(engines, "voisona", "engines")
    config = VoisonaConfig(
        enabled=_value(table, "enabled", bool, section, False),
        port=_port(table, section, 32766),
        user=_value(table, "user", str, section, ""),
        password=_value(table, "password", str, section, ""),
    )
    if config.enabled and not (config.user and config.password):
        raise ConfigError("VoiSona Talk を使うには、[engines.voisona] の user と password が必要です。")
    return config


def _parse_engines(data: dict[str, Any]) -> EnginesConfig:
    engines = _table(data, "engines", "engines")

    coeiroink = _table(engines, "coeiroink", "engines")
    aivoice = _table(engines, "aivoice", "engines")
    voicepeak = _table(engines, "voicepeak", "engines")
    aivoice_defaults = AiVoiceConfig()
    voicepeak_defaults = VoicepeakConfig()

    return EnginesConfig(
        voicevox=_parse_voicevox(engines),
        coeiroink=CoeiroinkConfig(
            enabled=_value(coeiroink, "enabled", bool, "engines.coeiroink", False),
            port=_port(coeiroink, "engines.coeiroink", 50032),
        ),
        aivoice=AiVoiceConfig(
            enabled=_value(aivoice, "enabled", bool, "engines.aivoice", False),
            dir=Path(_text(aivoice, "dir", "engines.aivoice", str(aivoice_defaults.dir))),
        ),
        voicepeak=VoicepeakConfig(
            enabled=_value(voicepeak, "enabled", bool, "engines.voicepeak", False),
            exe=Path(_text(voicepeak, "exe", "engines.voicepeak", str(voicepeak_defaults.exe))),
        ),
        voisona=_parse_voisona(engines),
    )


def load_config(path: Path) -> Config:
    """設定ファイルを読み込む。問題があれば ConfigError を送出する。"""
    try:
        with path.open("rb") as file:
            data = tomllib.load(file)
    except FileNotFoundError:
        raise ConfigError(
            f"設定ファイル {path} が見つかりません。"
            "config.example.toml をコピーして config.toml を作成してください。"
        ) from None
    except tomllib.TOMLDecodeError as error:
        raise ConfigError(f"設定ファイル {path} の書き方に誤りがあります：{error}") from None

    return Config(
        discord=_parse_discord(data),
        default_voice=_parse_default_voice(data),
        ffmpeg=FfmpegConfig(path=_value(_table(data, "ffmpeg", "ffmpeg"), "path", str, "ffmpeg", "")),
        engines=_parse_engines(data),
    )
