"""A.I.VOICE Editor API のエンジン。"""

from __future__ import annotations

import asyncio
import json
import tempfile
from collections.abc import Callable, Mapping
from concurrent.futures import ThreadPoolExecutor
from functools import partial
from pathlib import Path
from typing import Any, TypeVar

from .base import ParamSpec, Speaker, Style, TTSEngine, TTSError, VoiceParams

T = TypeVar("T")
ControlFactory = Callable[[], tuple[Any, Any]]

_DLL_NAME = "AI.Talk.Editor.Api.dll"
_NORMAL_STYLE = Style("普通", "")
_HIGH_LOW_SPEAKER = "タンゲ コトエ"
_STYLE_LABELS = {"J": "喜び", "A": "怒り", "S": "悲しみ"}
_HIGH_LOW_LABELS = {"J": "ハイテンション", "S": "ローテンション"}
# 保存設定がファイル命名規則のとき、Editor は API で指定したパスを無視して設定の出力先に保存する
_SAVE_SETTING_ERROR = (
    "A.I.VOICE Editor が指定した場所に音声を保存しませんでした。"
    "Editor の音声保存の設定で、ファイル命名規則を使わない設定に変更してください。"
)


def parse_styles(speaker: str, preset_json: str) -> tuple[Style, ...]:
    """ボイスプリセットから、「普通」を先頭にしたスタイルの一覧を作る。"""
    styles = [_NORMAL_STYLE]
    labels = _STYLE_LABELS | _HIGH_LOW_LABELS if speaker == _HIGH_LOW_SPEAKER else _STYLE_LABELS
    for style in json.loads(preset_json)["Styles"]:
        name = style["Name"]
        styles.append(Style(labels.get(name, name), name))
    return tuple(styles)


def apply_voice(preset_json: str, style_id: str, values: Mapping[str, float]) -> str:
    """ボイスプリセットに、スタイルとパラメータを反映した JSON を返す。"""
    preset = json.loads(preset_json)
    preset["Speed"] = values["speed"]
    preset["Pitch"] = values["pitch"]
    preset["PitchRange"] = values["intonation"]
    preset["Volume"] = values["volume"]
    for style in preset["Styles"]:
        style["Value"] = 1.0 if style["Name"] == style_id else 0.0
    return json.dumps(preset, ensure_ascii=False)


def _load_control(directory: Path) -> tuple[Any, Any]:
    dll = directory / _DLL_NAME
    if not dll.is_file():
        raise TTSError(f"A.I.VOICE の API が見つかりません: {dll}")

    import clr

    clr.AddReference(str(dll))
    from AI.Talk.Editor.Api import HostStatus, TtsControl

    return TtsControl(), HostStatus


class AiVoiceEngine(TTSEngine):
    param_specs = {
        "speed": ParamSpec(0.5, 4.0, 1.2),
        "pitch": ParamSpec(0.5, 2.0, 1.0),
        "intonation": ParamSpec(0.0, 2.0, 1.0),
        "volume": ParamSpec(0.0, 2.0, 1.0),
    }

    def __init__(
        self,
        directory: Path,
        control_factory: ControlFactory | None = None,
        name: str = "A.I.VOICE",
    ) -> None:
        super().__init__(name)
        self._factory = control_factory or partial(_load_control, directory)
        # A.I.VOICE の API は同期処理なので、専用のスレッド1本で1件ずつ呼ぶ
        self._executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="yomiage-aivoice")
        self._control: Any = None
        self._host_status: Any = None

    async def _call(self, function: Callable[..., T], *args: Any) -> T:
        loop = asyncio.get_running_loop()
        try:
            return await loop.run_in_executor(self._executor, function, *args)
        except TTSError:
            raise
        except Exception as error:
            raise TTSError(f"{self.name} の呼び出しに失敗しました: {error}") from error

    async def reload(self) -> None:
        self._speakers = await self._call(self._load_speakers)

    async def close(self) -> None:
        await self._call(self._disconnect)
        self._executor.shutdown(wait=False)

    async def synthesize(self, text: str, speaker: str, style: str, params: VoiceParams) -> bytes:
        _, found = self.find_style(speaker, style)
        return await self._call(self._synthesize, text, speaker, found.id, self.resolve_params(params))

    def _ensure_connected(self) -> Any:
        if self._control is None:
            control, self._host_status = self._factory()
            hosts = list(control.GetAvailableHostNames())
            if not hosts:
                raise TTSError("利用できる A.I.VOICE Editor が見つかりません")
            control.Initialize(hosts[0])
            self._control = control

        # API の操作が10分間ないと接続が切れるので、呼び出しのたびに確認する
        status = self._control.Status
        if status == self._host_status.NotRunning:
            self._control.StartHost()
            self._control.Connect()
        elif status == self._host_status.NotConnected:
            self._control.Connect()
        return self._control

    def _load_speakers(self) -> tuple[Speaker, ...]:
        control = self._ensure_connected()
        return tuple(
            Speaker(name=name, styles=parse_styles(name, control.GetVoicePreset(name)))
            for name in control.VoiceNames
        )

    def _set_sentence_pause(self, control: Any, value: int) -> int:
        master = json.loads(control.MasterControl)
        previous = master["SentencePause"]
        master["SentencePause"] = value
        control.MasterControl = json.dumps(master, ensure_ascii=False)
        return previous

    def _synthesize(self, text: str, speaker: str, style_id: str, values: Mapping[str, float]) -> bytes:
        control = self._ensure_connected()
        previous_pause = self._set_sentence_pause(control, 0)
        try:
            preset = apply_voice(control.GetVoicePreset(speaker), style_id, values)
            control.Text = text
            control.CurrentVoicePresetName = speaker
            control.SetVoicePreset(preset)
            with tempfile.TemporaryDirectory(prefix="yomiage-") as directory:
                path = Path(directory) / "voice.wav"
                control.SaveAudioToFile(str(path))
                if not path.is_file():
                    raise TTSError(_SAVE_SETTING_ERROR)
                return path.read_bytes()
        finally:
            self._set_sentence_pause(control, previous_pause)

    def _disconnect(self) -> None:
        if self._control is not None and self._control.Status not in (
            self._host_status.NotRunning,
            self._host_status.NotConnected,
        ):
            self._control.Disconnect()
