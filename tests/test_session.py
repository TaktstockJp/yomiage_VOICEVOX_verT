import asyncio
import threading
from collections.abc import Awaitable, Callable

from yomiage.reading.session import ReadingSession, Utterance
from yomiage.tts.base import (
    ParamSpec,
    Speaker,
    Style,
    TTSEngine,
    TTSError,
    VoiceParams,
    VoiceSelection,
)
from yomiage.tts.registry import EngineRegistry

VOICE = VoiceSelection("Fake", "話者", "スタイル")
TIMEOUT = 2.0


class FakeEngine(TTSEngine):
    param_specs = {"speed": ParamSpec(0.5, 2.0, 1.0)}

    def __init__(self) -> None:
        super().__init__("Fake")
        self.requests: list[tuple[str, VoiceParams]] = []
        self.failing: set[str] = set()
        self.gates: dict[str, asyncio.Event] = {}

    async def reload(self) -> None:
        self._speakers = (Speaker("話者", (Style("スタイル", 1),)),)

    async def synthesize(self, text: str, speaker: str, style: str, params: VoiceParams) -> bytes:
        self.requests.append((text, params))
        if text in self.gates:
            await self.gates[text].wait()
        if text in self.failing:
            raise TTSError("合成に失敗")
        return text.encode()


class FakeVoiceClient:
    """再生を手動で完了させられる VoiceClient。after は実物と同じく別スレッドから呼ぶ。"""

    def __init__(self) -> None:
        self.played: list[bytes] = []
        self.current: tuple[bytes, Callable[[Exception | None], None]] | None = None
        self.overlapped = False
        self.started = asyncio.Event()

    def play(self, source: bytes, *, after: Callable[[Exception | None], None]) -> None:
        if self.current is not None:
            self.overlapped = True
        self.current = (source, after)
        self.played.append(source)
        self.started.set()

    def finish(self, error: Exception | None = None) -> None:
        assert self.current is not None
        _, after = self.current
        self.current = None
        self.started.clear()
        thread = threading.Thread(target=after, args=(error,))
        thread.start()
        thread.join()

    def stop(self) -> None:
        if self.current is not None:
            self.finish()


class Harness:
    def __init__(self, engine: FakeEngine, voice_client: FakeVoiceClient, session: ReadingSession) -> None:
        self.engine = engine
        self.vc = voice_client
        self.session = session

    def say(self, *texts: str) -> None:
        for text in texts:
            self.session.enqueue(Utterance(text, VOICE, {}))

    async def wait_playing(self, text: str) -> None:
        async def wait() -> None:
            while self.vc.current is None or self.vc.current[0] != text.encode():
                await asyncio.sleep(0)

        await asyncio.wait_for(wait(), TIMEOUT)

    async def wait_requested(self, count: int) -> None:
        async def wait() -> None:
            while len(self.engine.requests) < count:
                await asyncio.sleep(0)

        await asyncio.wait_for(wait(), TIMEOUT)

    async def settle(self) -> None:
        for _ in range(50):
            await asyncio.sleep(0)


Scenario = Callable[[Harness], Awaitable[None]]


def run(scenario: Scenario) -> Harness:
    async def main() -> Harness:
        engine = FakeEngine()
        registry = EngineRegistry()
        await registry.add(engine)
        voice_client = FakeVoiceClient()
        session = ReadingSession(voice_client, None, registry, lambda wav: wav)  # type: ignore[arg-type]
        session.start()
        harness = Harness(engine, voice_client, session)
        try:
            await scenario(harness)
        finally:
            await session.close()
        return harness

    return asyncio.run(main())


def test_utterances_play_in_order_without_overlap() -> None:
    async def scenario(h: Harness) -> None:
        h.say("一", "二", "三")
        await h.wait_playing("一")
        h.vc.finish()
        await h.wait_playing("二")
        h.vc.finish()
        await h.wait_playing("三")
        h.vc.finish()

    harness = run(scenario)

    assert harness.vc.played == ["一".encode(), "二".encode(), "三".encode()]
    assert harness.vc.overlapped is False


def test_next_clips_are_synthesized_ahead_but_bounded() -> None:
    async def scenario(h: Harness) -> None:
        h.say("一", "二", "三", "四", "五", "六")
        await h.wait_playing("一")
        await h.settle()

        # 再生中の1件、キューの2件、キューの空き待ちの1件まで
        assert [text for text, _ in h.engine.requests] == ["一", "二", "三", "四"]

    run(scenario)


def test_stop_discards_playing_and_queued_audio() -> None:
    async def scenario(h: Harness) -> None:
        h.say("一", "二", "三", "四", "五")
        await h.wait_playing("一")
        await h.settle()

        h.session.stop()
        await h.settle()

        assert h.vc.current is None
        h.say("次")
        await h.wait_playing("次")
        h.vc.finish()

    harness = run(scenario)

    assert harness.vc.played == ["一".encode(), "次".encode()]


def test_audio_being_synthesized_during_stop_is_not_played() -> None:
    async def scenario(h: Harness) -> None:
        h.engine.gates["遅い"] = asyncio.Event()
        h.say("遅い")
        await h.wait_requested(1)

        h.session.stop()
        h.engine.gates["遅い"].set()
        await h.settle()

        assert h.vc.played == []
        h.say("次")
        await h.wait_playing("次")
        h.vc.finish()

    harness = run(scenario)

    assert harness.vc.played == ["次".encode()]


def test_synthesis_failure_does_not_stop_the_worker() -> None:
    async def scenario(h: Harness) -> None:
        h.engine.failing.add("失敗")
        h.say("失敗", "成功")
        await h.wait_playing("成功")
        h.vc.finish()

    assert run(scenario).vc.played == ["成功".encode()]


def test_playback_error_does_not_stop_the_worker() -> None:
    async def scenario(h: Harness) -> None:
        h.say("一", "二")
        await h.wait_playing("一")
        h.vc.finish(RuntimeError("再生エラー"))
        await h.wait_playing("二")
        h.vc.finish()

    assert len(run(scenario).vc.played) == 2


def test_voice_and_params_are_those_given_at_enqueue() -> None:
    async def scenario(h: Harness) -> None:
        h.session.enqueue(Utterance("一", VOICE, {"speed": 1.5}))
        await h.wait_playing("一")
        h.vc.finish()

    assert run(scenario).engine.requests == [("一", {"speed": 1.5})]


def test_unregistered_engine_is_skipped() -> None:
    async def scenario(h: Harness) -> None:
        h.session.enqueue(Utterance("無効", VoiceSelection("なし", "a", "b"), {}))
        h.say("有効")
        await h.wait_playing("有効")
        h.vc.finish()

    assert run(scenario).vc.played == ["有効".encode()]


def test_close_stops_current_playback() -> None:
    async def scenario(h: Harness) -> None:
        h.say("一")
        await h.wait_playing("一")
        await h.session.close()

        assert h.vc.current is None

    run(scenario)
