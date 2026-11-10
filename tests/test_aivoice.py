import asyncio
import json
import threading
from pathlib import Path
from types import SimpleNamespace

import pytest

from yomiage.tts.aivoice import AiVoiceEngine, apply_voice, parse_styles
from yomiage.tts.base import TTSError, VoiceNotFoundError

STATUS = SimpleNamespace(NotRunning="not_running", NotConnected="not_connected", Idle="idle", Busy="busy")
PRESET = json.dumps(
    {
        "Speed": 1.0,
        "Pitch": 1.0,
        "PitchRange": 1.0,
        "Volume": 1.0,
        "Styles": [{"Name": "J", "Value": 0.5}, {"Name": "A", "Value": 0.0}, {"Name": "S", "Value": 0.0}],
    }
)


class FakeControl:
    def __init__(self, status: str = STATUS.Idle) -> None:
        self.Status = status
        self.VoiceNames = ["紲星 あかり", "タンゲ コトエ"]
        self.MasterControl = json.dumps({"SentencePause": 200, "Volume": 1.0})
        self.Text = ""
        self.CurrentVoicePresetName = ""
        self.preset_set = ""
        self.pause_during_save: int | None = None
        self.threads: set[int] = set()
        self.calls: list[str] = []
        self.fail_save = False
        self.ignores_path = False

    def _record(self, name: str) -> None:
        self.calls.append(name)
        self.threads.add(threading.get_ident())

    def GetAvailableHostNames(self) -> list[str]:
        self._record("hosts")
        return ["A.I.VOICE Editor"]

    def Initialize(self, name: str) -> None:
        self._record(f"init:{name}")

    def StartHost(self) -> None:
        self._record("start")
        self.Status = STATUS.NotConnected

    def Connect(self) -> None:
        self._record("connect")
        self.Status = STATUS.Idle

    def Disconnect(self) -> None:
        self._record("disconnect")

    def GetVoicePreset(self, name: str) -> str:
        self._record("preset")
        return PRESET

    def SetVoicePreset(self, preset: str) -> None:
        self.preset_set = preset

    def SaveAudioToFile(self, path: str) -> None:
        self._record("save")
        if self.fail_save:
            raise RuntimeError(".NET の例外")
        self.pause_during_save = json.loads(self.MasterControl)["SentencePause"]
        if not self.ignores_path:
            Path(path).write_bytes(b"RIFF-aivoice")


def engine_for(control: FakeControl) -> AiVoiceEngine:
    return AiVoiceEngine(Path("unused"), control_factory=lambda: (control, STATUS))


def run(engine: AiVoiceEngine, *texts: str) -> list[bytes]:
    async def main() -> list[bytes]:
        await engine.start()
        try:
            return [await engine.synthesize(text, "紲星 あかり", "怒り", {"speed": 1.5}) for text in texts]
        finally:
            await engine.close()

    return asyncio.run(main())


def test_parse_styles_adds_normal_and_labels() -> None:
    assert [s.name for s in parse_styles("紲星 あかり", PRESET)] == ["普通", "喜び", "怒り", "悲しみ"]
    assert [s.id for s in parse_styles("紲星 あかり", PRESET)] == ["", "J", "A", "S"]


def test_parse_styles_uses_special_labels_for_kotoe() -> None:
    assert [s.name for s in parse_styles("タンゲ コトエ", PRESET)] == ["普通", "ハイテンション", "怒り", "ローテンション"]


def test_apply_voice_maps_parameters_and_selects_one_style() -> None:
    preset = json.loads(apply_voice(PRESET, "A", {"speed": 1.5, "pitch": 1.1, "intonation": 0.9, "volume": 1.2}))

    assert (preset["Speed"], preset["Pitch"], preset["PitchRange"], preset["Volume"]) == (1.5, 1.1, 0.9, 1.2)
    assert [s["Value"] for s in preset["Styles"]] == [0.0, 1.0, 0.0]


def test_apply_voice_normal_style_clears_all_weights() -> None:
    preset = json.loads(apply_voice(PRESET, "", {"speed": 1, "pitch": 1, "intonation": 1, "volume": 1}))

    assert [s["Value"] for s in preset["Styles"]] == [0.0, 0.0, 0.0]


def test_synthesize_uses_file_output_and_restores_sentence_pause() -> None:
    control = FakeControl()

    assert run(engine_for(control), "こんにちは") == [b"RIFF-aivoice"]
    assert control.Text == "こんにちは"
    assert control.CurrentVoicePresetName == "紲星 あかり"
    assert json.loads(control.preset_set)["Speed"] == 1.5
    assert control.pause_during_save == 0
    assert json.loads(control.MasterControl)["SentencePause"] == 200


def test_sentence_pause_is_restored_on_failure() -> None:
    control = FakeControl()
    control.fail_save = True

    with pytest.raises(TTSError):
        run(engine_for(control), "こんにちは")

    assert json.loads(control.MasterControl)["SentencePause"] == 200


def test_editor_ignoring_the_path_explains_the_setting_to_change() -> None:
    control = FakeControl()
    control.ignores_path = True

    with pytest.raises(TTSError, match="ファイル命名規則"):
        run(engine_for(control), "こんにちは")

    assert json.loads(control.MasterControl)["SentencePause"] == 200


def test_all_calls_run_on_one_thread_away_from_the_event_loop() -> None:
    control = FakeControl()

    run(engine_for(control), "一", "二")

    assert len(control.threads) == 1
    assert threading.get_ident() not in control.threads


def test_host_is_started_when_not_running() -> None:
    control = FakeControl(STATUS.NotRunning)

    run(engine_for(control), "一")

    assert control.calls[:4] == ["hosts", "init:A.I.VOICE Editor", "start", "connect"]


def test_reconnects_when_the_connection_was_dropped() -> None:
    control = FakeControl()

    async def main() -> None:
        engine = engine_for(control)
        await engine.start()
        control.Status = STATUS.NotConnected
        await engine.synthesize("一", "紲星 あかり", "普通", {})
        await engine.close()

    asyncio.run(main())

    assert "connect" in control.calls


def test_unknown_style_raises() -> None:
    async def main() -> None:
        engine = engine_for(FakeControl())
        await engine.start()
        with pytest.raises(VoiceNotFoundError):
            await engine.synthesize("一", "紲星 あかり", "存在しない", {})
        await engine.close()

    asyncio.run(main())


def test_missing_dll_becomes_tts_error(tmp_path: Path) -> None:
    async def main() -> None:
        engine = AiVoiceEngine(tmp_path)
        with pytest.raises(TTSError, match="見つかりません"):
            await engine.start()
        await engine.close()

    asyncio.run(main())
