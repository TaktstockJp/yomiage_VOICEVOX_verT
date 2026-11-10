"""HTTP 系エンジンのリクエスト組み立てを、テスト用の HTTP サーバーで確認する。"""

import asyncio
from collections.abc import Awaitable, Callable

import aiohttp
import pytest
from aiohttp import web
from aiohttp.test_utils import TestServer

from yomiage.tts.base import TTSError, VoiceNotFoundError
from yomiage.tts.coeiroink import CoeiroinkEngine
from yomiage.tts.voicevox import VoicevoxEngine

WAV = b"RIFF-test"
Scenario = Callable[[aiohttp.ClientSession, int], Awaitable[None]]


def run_with_server(routes: list[web.RouteDef], scenario: Scenario) -> None:
    async def main() -> None:
        app = web.Application()
        app.add_routes(routes)
        server = TestServer(app)
        await server.start_server()
        try:
            async with aiohttp.ClientSession() as session:
                await scenario(session, server.port)
        finally:
            await server.close()

    asyncio.run(main())


def voicevox_routes(received: dict) -> list[web.RouteDef]:
    async def speakers(request: web.Request) -> web.Response:
        return web.json_response(
            [{"name": "ずんだもん", "speaker_uuid": "x", "styles": [{"name": "ノーマル", "id": 3}]}]
        )

    async def audio_query(request: web.Request) -> web.Response:
        received["query_params"] = dict(request.query)
        return web.json_response({"speedScale": 1.0, "pitchScale": 0.0, "kana": "テスト"})

    async def synthesis(request: web.Request) -> web.Response:
        received["synthesis_params"] = dict(request.query)
        received["synthesis_body"] = await request.json()
        return web.Response(body=WAV, content_type="audio/wav")

    return [
        web.get("/speakers", speakers),
        web.post("/audio_query", audio_query),
        web.post("/synthesis", synthesis),
    ]


def test_voicevox_loads_speakers() -> None:
    async def scenario(session: aiohttp.ClientSession, port: int) -> None:
        engine = VoicevoxEngine("VOICEVOX", port, session)
        await engine.start()

        assert [s.name for s in engine.speakers()] == ["ずんだもん"]
        assert engine.speakers()[0].styles[0].id == 3

    run_with_server(voicevox_routes({}), scenario)


def test_voicevox_applies_parameters_to_the_query() -> None:
    received: dict = {}

    async def scenario(session: aiohttp.ClientSession, port: int) -> None:
        engine = VoicevoxEngine("VOICEVOX", port, session)
        await engine.start()

        wav = await engine.synthesize("こんにちは&テスト", "ずんだもん", "ノーマル", {"speed": 1.5})

        assert wav == WAV

    run_with_server(voicevox_routes(received), scenario)

    assert received["query_params"] == {"text": "こんにちは&テスト", "speaker": "3"}
    assert received["synthesis_params"] == {"speaker": "3"}
    assert received["synthesis_body"] == {
        "speedScale": 1.5,
        "pitchScale": 0.0,
        "intonationScale": 1.0,
        "volumeScale": 1.0,
        "kana": "テスト",
    }


def test_voicevox_unknown_voice_raises_before_any_request() -> None:
    async def scenario(session: aiohttp.ClientSession, port: int) -> None:
        engine = VoicevoxEngine("VOICEVOX", port, session)
        await engine.start()

        with pytest.raises(VoiceNotFoundError):
            await engine.synthesize("a", "ずんだもん", "存在しない", {})

    run_with_server(voicevox_routes({}), scenario)


def test_voicevox_http_error_becomes_tts_error() -> None:
    async def failing(request: web.Request) -> web.Response:
        return web.Response(status=500)

    async def scenario(session: aiohttp.ClientSession, port: int) -> None:
        with pytest.raises(TTSError):
            await VoicevoxEngine("VOICEVOX", port, session).start()

    run_with_server([web.get("/speakers", failing)], scenario)


@pytest.mark.parametrize("body", [{"not": "a list"}, [{"unexpected": 1}]])
def test_voicevox_unexpected_speakers_format_becomes_tts_error(body: object) -> None:
    async def speakers(request: web.Request) -> web.Response:
        return web.json_response(body)

    async def scenario(session: aiohttp.ClientSession, port: int) -> None:
        with pytest.raises(TTSError):
            await VoicevoxEngine("VOICEVOX", port, session).start()

    run_with_server([web.get("/speakers", speakers)], scenario)


def test_connection_failure_becomes_tts_error() -> None:
    async def main() -> None:
        async with aiohttp.ClientSession() as session:
            # ポート 1 は通常どのプログラムも待ち受けていない
            with pytest.raises(TTSError):
                await VoicevoxEngine("VOICEVOX", 1, session).start()

    asyncio.run(main())


def coeiroink_routes(received: dict) -> list[web.RouteDef]:
    async def speakers(request: web.Request) -> web.Response:
        return web.json_response(
            [
                {
                    "speakerName": "つくよみちゃん",
                    "speakerUuid": "uuid-1",
                    "styles": [{"styleName": "れいせい", "styleId": 7}],
                }
            ]
        )

    async def synthesis(request: web.Request) -> web.Response:
        received["body"] = await request.json()
        return web.Response(body=WAV, content_type="audio/wav")

    return [web.get("/v1/speakers", speakers), web.post("/v1/synthesis", synthesis)]


def test_coeiroink_builds_the_synthesis_request() -> None:
    received: dict = {}

    async def scenario(session: aiohttp.ClientSession, port: int) -> None:
        engine = CoeiroinkEngine(port, session)
        await engine.start()

        wav = await engine.synthesize("テスト", "つくよみちゃん", "れいせい", {"pitch": 0.1, "volume": 9.0})

        assert wav == WAV

    run_with_server(coeiroink_routes(received), scenario)

    assert received["body"] == {
        "speakerUuid": "uuid-1",
        "styleId": 7,
        "text": "テスト",
        "speedScale": 1.2,
        "volumeScale": 2.0,
        "pitchScale": 0.1,
        "intonationScale": 1.0,
        "prePhonemeLength": 0.0,
        "postPhonemeLength": 0.0,
        "outputSamplingRate": 44100,
    }
