import asyncio

import pytest

from yomiage.tts.base import (
    ParamSpec,
    Speaker,
    Style,
    TTSEngine,
    TTSError,
    VoiceNotFoundError,
    VoiceParams,
    VoiceSelection,
)
from yomiage.tts.registry import EngineRegistry


class FakeEngine(TTSEngine):
    param_specs = {"speed": ParamSpec(0.5, 2.0, 1.2)}

    def __init__(self, name: str, speakers=(), fail_start: bool = False) -> None:
        super().__init__(name)
        self.available = speakers
        self.fail = fail_start
        self.closed = False

    async def reload(self) -> None:
        if self.fail:
            raise TTSError("接続できません")
        self._speakers = tuple(self.available)

    async def close(self) -> None:
        self.closed = True

    async def synthesize(self, text: str, speaker: str, style: str, params: VoiceParams) -> bytes:
        return b""


ZUNDA = Speaker("ずんだもん", (Style("ノーマル", 3), Style("あまあま", 1)))
METAN = Speaker("四国めたん", (Style("ノーマル", 2),))


def registry_with(*engines: TTSEngine) -> EngineRegistry:
    registry = EngineRegistry()
    for engine in engines:
        assert asyncio.run(registry.add(engine))
    return registry


def test_engine_that_fails_to_start_is_not_registered() -> None:
    registry = EngineRegistry()
    broken = FakeEngine("A", fail_start=True)

    assert asyncio.run(registry.add(broken)) is False
    assert registry.engines() == ()
    assert broken.closed is True


def test_engine_without_speakers_is_not_registered() -> None:
    assert asyncio.run(EngineRegistry().add(FakeEngine("A"))) is False


def test_duplicate_engine_name_is_rejected() -> None:
    registry = registry_with(FakeEngine("A", [ZUNDA]))

    with pytest.raises(ValueError):
        asyncio.run(registry.add(FakeEngine("A", [ZUNDA])))


def test_find_searches_in_registration_order() -> None:
    registry = registry_with(FakeEngine("A", [METAN]), FakeEngine("B", [ZUNDA, METAN]))

    assert registry.find("四国めたん", "ノーマル") == VoiceSelection("A", "四国めたん", "ノーマル")
    assert registry.find("ずんだもん", "あまあま") == VoiceSelection("B", "ずんだもん", "あまあま")


def test_find_can_be_limited_to_one_engine() -> None:
    registry = registry_with(FakeEngine("A", [METAN]), FakeEngine("B", [METAN]))

    assert registry.find("四国めたん", "ノーマル", "B") == VoiceSelection("B", "四国めたん", "ノーマル")
    assert registry.find("四国めたん", "ノーマル", "C") is None
    assert registry.find("四国めたん", "あまあま") is None


def test_resolve_uses_the_first_available_voice() -> None:
    registry = registry_with(FakeEngine("A", [ZUNDA]))
    user = VoiceSelection("A", "ずんだもん", "あまあま")
    default = VoiceSelection("A", "ずんだもん", "ノーマル")

    assert registry.resolve(user, default) == user
    assert registry.resolve(None, default) == default
    assert registry.resolve(VoiceSelection("Z", "x", "y"), default) == default


def test_resolve_falls_back_to_the_first_voice_of_the_first_engine() -> None:
    registry = registry_with(FakeEngine("A", [ZUNDA]), FakeEngine("B", [METAN]))

    assert registry.resolve(None, VoiceSelection("Z", "x", "y")) == VoiceSelection("A", "ずんだもん", "ノーマル")


def test_resolve_without_engines_raises() -> None:
    with pytest.raises(VoiceNotFoundError):
        EngineRegistry().resolve(None)


def test_reload_failure_keeps_previous_speakers_and_continues() -> None:
    first = FakeEngine("A", [ZUNDA])
    second = FakeEngine("B", [ZUNDA])
    registry = registry_with(first, second)
    first.fail = True
    second.available = [METAN]

    assert asyncio.run(registry.reload_all()) == ["A"]
    assert first.speakers() == (ZUNDA,)
    assert second.speakers() == (METAN,)


def test_close_all_closes_every_engine() -> None:
    first = FakeEngine("A", [ZUNDA])
    second = FakeEngine("B", [ZUNDA])
    registry = registry_with(first, second)

    asyncio.run(registry.close_all())

    assert first.closed and second.closed
    assert registry.engines() == ()


def test_resolve_params_fills_defaults_and_clamps() -> None:
    engine = FakeEngine("A")

    assert engine.resolve_params({}) == {"speed": 1.2}
    assert engine.resolve_params({"speed": 9.0, "unknown": 1.0}) == {"speed": 2.0}
    assert engine.resolve_params({"speed": 0.1}) == {"speed": 0.5}
