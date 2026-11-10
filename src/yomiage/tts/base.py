"""TTS エンジンの共通インターフェース。"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Mapping, Sequence
from dataclasses import dataclass

VoiceParams = Mapping[str, float]


class TTSError(Exception):
    """音声合成や話者一覧の取得に失敗したことを表す例外。"""


class VoiceNotFoundError(TTSError):
    """指定された話者またはスタイルが存在しないことを表す例外。"""


@dataclass(frozen=True)
class VoiceSelection:
    engine: str
    speaker: str
    style: str


@dataclass(frozen=True)
class ParamSpec:
    min: float
    max: float
    default: float

    def contains(self, value: float) -> bool:
        return self.min <= value <= self.max


@dataclass(frozen=True)
class Style:
    name: str
    id: int | str


@dataclass(frozen=True)
class Speaker:
    name: str
    styles: tuple[Style, ...]
    id: str = ""


class TTSEngine(ABC):
    """TTS ソフト1つを表す基底クラス。"""

    param_specs: Mapping[str, ParamSpec]

    def __init__(self, name: str) -> None:
        self.name = name
        self._speakers: tuple[Speaker, ...] = ()

    async def start(self) -> None:
        """接続を確認し、話者一覧を取得する。"""
        await self.reload()

    async def close(self) -> None:
        """エンジンが持つ資源を解放する。"""

    @abstractmethod
    async def reload(self) -> None:
        """話者一覧を取り直す。失敗したときは TTSError を送出し、以前の一覧を残す。"""

    @abstractmethod
    async def synthesize(self, text: str, speaker: str, style: str, params: VoiceParams) -> bytes:
        """音声を合成して WAV のバイト列を返す。"""

    def speakers(self) -> Sequence[Speaker]:
        return self._speakers

    def find_style(self, speaker_name: str, style_name: str) -> tuple[Speaker, Style]:
        for speaker in self._speakers:
            if speaker.name != speaker_name:
                continue
            for style in speaker.styles:
                if style.name == style_name:
                    return speaker, style
        raise VoiceNotFoundError(f"{self.name}: {speaker_name} / {style_name}")

    def has_voice(self, speaker_name: str, style_name: str) -> bool:
        try:
            self.find_style(speaker_name, style_name)
        except VoiceNotFoundError:
            return False
        return True

    def resolve_params(self, overrides: VoiceParams) -> dict[str, float]:
        """エンジンが対応する全パラメータの値を、範囲内に収めて返す。"""
        return {
            name: min(max(overrides.get(name, spec.default), spec.min), spec.max)
            for name, spec in self.param_specs.items()
        }
