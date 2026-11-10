import asyncio
import io
import wave
from pathlib import Path

import pytest

from yomiage.tts import voicepeak as voicepeak_module
from yomiage.tts.base import TTSError, VoiceNotFoundError
from yomiage.tts.voicepeak import VoicepeakEngine


def make_wav(frames: bytes) -> bytes:
    output = io.BytesIO()
    with wave.open(output, "wb") as writer:
        writer.setnchannels(1)
        writer.setsampwidth(2)
        writer.setframerate(24000)
        writer.writeframes(frames)
    return output.getvalue()


class FakeExecutable:
    """asyncio.create_subprocess_exec の代わりに、呼び出しを記録して結果を返す。"""

    def __init__(self) -> None:
        self.calls: list[tuple[str, ...]] = []
        self.returncode = 0
        self.write_output = True
        self.running = 0
        self.max_running = 0
        self.hang = False
        self.killed = False

    async def __call__(self, program: str, *args: str, **kwargs: object) -> "FakeProcess":
        self.calls.append(args)
        return FakeProcess(self, args)


class FakeProcess:
    def __init__(self, executable: FakeExecutable, args: tuple[str, ...]) -> None:
        self.executable = executable
        self.args = args
        self.returncode: int | None = None

    async def communicate(self) -> tuple[bytes, bytes]:
        exe = self.executable
        exe.running += 1
        exe.max_running = max(exe.max_running, exe.running)
        await asyncio.sleep(0)
        exe.running -= 1
        if exe.hang:
            await asyncio.sleep(3600)

        self.returncode = exe.returncode
        if self.args[0] == "--list-narrator":
            return "Frimomen\r\nZundamon\r\n\r\n".encode(), b""
        if self.args[0] == "--list-emotion":
            return ("happy\r\nsad\r\n" if self.args[1] == "Frimomen" else "amaama\r\n").encode(), b""
        if exe.write_output and exe.returncode == 0:
            Path(self.args[self.args.index("-o") + 1]).write_bytes(make_wav(b"\x01\x00"))
        return b"", b""

    def kill(self) -> None:
        self.executable.killed = True
        self.returncode = -9

    async def wait(self) -> int:
        return self.returncode or 0


@pytest.fixture
def exe(monkeypatch: pytest.MonkeyPatch) -> FakeExecutable:
    fake = FakeExecutable()
    monkeypatch.setattr(voicepeak_module.asyncio, "create_subprocess_exec", fake)
    return fake


def synthesize(text: str, style: str = "標準", params: dict | None = None, narrator: str = "Frimomen") -> bytes:
    async def main() -> bytes:
        engine = VoicepeakEngine(Path("voicepeak.exe"))
        await engine.start()
        return await engine.synthesize(text, narrator, style, params or {})

    return asyncio.run(main())


def synth_calls(exe: FakeExecutable) -> list[tuple[str, ...]]:
    return [call for call in exe.calls if call[0].startswith("--say=")]


def test_reload_lists_narrators_and_adds_standard_style(exe: FakeExecutable) -> None:
    async def main() -> VoicepeakEngine:
        engine = VoicepeakEngine(Path("voicepeak.exe"))
        await engine.start()
        return engine

    engine = asyncio.run(main())

    assert [s.name for s in engine.speakers()] == ["Frimomen", "Zundamon"]
    assert [s.name for s in engine.speakers()[0].styles] == ["標準", "happy", "sad"]
    assert [s.name for s in engine.speakers()[1].styles] == ["標準", "amaama"]


def test_standard_style_passes_no_emotion(exe: FakeExecutable) -> None:
    synthesize("こんにちは", params={"speed": 150, "pitch": -20})

    call = synth_calls(exe)[0]
    assert call[0] == "--say=こんにちは"
    assert "-e" not in call
    assert call[call.index("-n") + 1] == "Frimomen"
    assert call[call.index("--speed") + 1] == "150"
    assert call[call.index("--pitch") + 1] == "-20"


def test_emotion_style_is_passed(exe: FakeExecutable) -> None:
    synthesize("こんにちは", style="happy")

    call = synth_calls(exe)[0]
    assert call[call.index("-e") + 1] == "happy=100"


def test_parameters_are_limited_to_the_supported_range(exe: FakeExecutable) -> None:
    synthesize("こんにちは", params={"speed": 999})

    call = synth_calls(exe)[0]
    assert call[call.index("--speed") + 1] == "200"


def test_long_text_is_split_and_joined(exe: FakeExecutable) -> None:
    wav = synthesize("あ" * 100 + "。" + "い" * 100 + "。")

    calls = synth_calls(exe)
    assert len(calls) == 2
    assert all(len(call[0].removeprefix("--say=")) <= 140 for call in calls)
    with wave.open(io.BytesIO(wav), "rb") as reader:
        assert reader.getnframes() == 2


def test_each_call_uses_a_new_output_path(exe: FakeExecutable) -> None:
    async def main() -> None:
        engine = VoicepeakEngine(Path("voicepeak.exe"))
        await engine.start()
        await asyncio.gather(*(engine.synthesize(str(i), "Frimomen", "標準", {}) for i in range(5)))

    asyncio.run(main())

    outputs = [call[call.index("-o") + 1] for call in synth_calls(exe)]
    assert len(set(outputs)) == 5
    assert exe.max_running == 1


def test_temporary_files_are_removed(exe: FakeExecutable) -> None:
    synthesize("こんにちは")

    output = synth_calls(exe)[0]
    assert not Path(output[output.index("-o") + 1]).exists()


def test_failure_exit_code_becomes_tts_error(exe: FakeExecutable) -> None:
    async def main() -> None:
        engine = VoicepeakEngine(Path("voicepeak.exe"))
        await engine.start()
        exe.returncode = 1
        with pytest.raises(TTSError):
            await engine.synthesize("a", "Frimomen", "標準", {})

    asyncio.run(main())


def test_missing_output_becomes_tts_error(exe: FakeExecutable) -> None:
    exe.write_output = False

    with pytest.raises(TTSError):
        synthesize("こんにちは")


def test_hanging_process_is_killed(exe: FakeExecutable, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(voicepeak_module, "_TIMEOUT_SECONDS", 0.01)

    async def main() -> None:
        engine = VoicepeakEngine(Path("voicepeak.exe"))
        await engine.start()
        exe.hang = True
        with pytest.raises(TTSError, match="タイムアウト"):
            await engine.synthesize("a", "Frimomen", "標準", {})

    asyncio.run(main())

    assert exe.killed is True


def test_missing_executable_becomes_tts_error(tmp_path: Path) -> None:
    async def main() -> None:
        with pytest.raises(TTSError):
            await VoicepeakEngine(tmp_path / "none.exe").start()

    asyncio.run(main())


def test_unknown_style_raises(exe: FakeExecutable) -> None:
    with pytest.raises(VoiceNotFoundError):
        synthesize("a", style="存在しない")
