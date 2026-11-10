"""VoiSona Talk のリクエスト組み立てを、テスト用の HTTP サーバーで確認する。"""

import asyncio
import base64
import io
import wave

import aiohttp
import pytest
from aiohttp import web
from aiohttp.test_utils import TestServer

from yomiage.tts.base import TTSError
from yomiage.tts.voisona import VoisonaEngine

USER = "user@example.com"
PASSWORD = "secret-password"
BASE = "/api/talk/v1"
UUID = "0123"


def make_wav(frames: bytes) -> bytes:
    output = io.BytesIO()
    with wave.open(output, "wb") as writer:
        writer.setnchannels(1)
        writer.setsampwidth(2)
        writer.setframerate(48000)
        writer.writeframes(frames)
    return output.getvalue()


class FakeVoisona:
    def __init__(self) -> None:
        self.bodies: list[dict] = []
        self.states = ["queued", "running", "succeeded"]
        self.deleted: list[str] = []
        self.polls = 0
        self.authorizations: set[str] = set()
        self.wav_status = 200

    def routes(self) -> list[web.RouteDef]:
        return [
            web.get(f"{BASE}/voices", self.voices),
            web.get(f"{BASE}/voices/{{name}}/{{version}}", self.voice),
            web.post(f"{BASE}/speech-syntheses", self.create),
            web.get(f"{BASE}/speech-syntheses/{{uuid}}", self.status),
            web.get(f"{BASE}/speech-syntheses/{{uuid}}/wav", self.wav),
            web.delete(f"{BASE}/speech-syntheses/{{uuid}}", self.delete),
        ]

    def _authorize(self, request: web.Request) -> None:
        self.authorizations.add(request.headers.get("Authorization", ""))

    async def voices(self, request: web.Request) -> web.Response:
        self._authorize(request)
        return web.json_response(
            {
                "items": [
                    {
                        "display_names": [
                            {"language": "en_US", "name": "Tanaka San"},
                            {"language": "ja_JP", "name": "田中傘"},
                        ],
                        "languages": ["ja_JP"],
                        "voice_name": "tanaka-san_ja_JP",
                        "voice_version": "2.0.1",
                    },
                    {
                        "languages": ["ja_JP"],
                        "voice_name": "tanaka-san_ja_JP",
                        "voice_version": "1.0.0",
                    },
                    {"languages": ["en_US"], "voice_name": "english_en_US", "voice_version": "1.0.0"},
                    {"languages": ["ja_JP"], "voice_name": "no-display_ja_JP", "voice_version": "1.0.0"},
                ]
            }
        )

    async def voice(self, request: web.Request) -> web.Response:
        return web.json_response({"style_names": ["Normal", "Happy", "Sad"]})

    async def create(self, request: web.Request) -> web.Response:
        self.bodies.append(await request.json())
        return web.json_response({"uuid": UUID}, status=201)

    async def status(self, request: web.Request) -> web.Response:
        self.polls += 1
        state = self.states.pop(0) if len(self.states) > 1 else self.states[0]
        return web.json_response({"state": state})

    async def wav(self, request: web.Request) -> web.Response:
        if self.wav_status != 200:
            return web.Response(status=self.wav_status)
        return web.Response(body=make_wav(b"\x01\x00"), content_type="audio/wav")

    async def delete(self, request: web.Request) -> web.Response:
        self.deleted.append(request.match_info["uuid"])
        return web.json_response({})


def run(fake: FakeVoisona, scenario) -> None:
    async def main() -> None:
        app = web.Application()
        app.add_routes(fake.routes())
        server = TestServer(app)
        await server.start_server()
        try:
            async with aiohttp.ClientSession() as session:
                engine = VoisonaEngine(server.port, USER, PASSWORD, session)
                await engine.start()
                await scenario(engine)
        finally:
            await server.close()

    asyncio.run(main())


def test_reload_merges_versions_and_keeps_japanese_voices() -> None:
    async def scenario(engine: VoisonaEngine) -> None:
        assert [(s.name, s.id) for s in engine.speakers()] == [
            ("田中傘", "tanaka-san_ja_JP"),
            ("no-display_ja_JP", "no-display_ja_JP"),
        ]
        assert [s.name for s in engine.speakers()[0].styles] == ["Normal", "Happy", "Sad"]

    run(FakeVoisona(), scenario)


def test_basic_auth_is_sent() -> None:
    fake = FakeVoisona()

    async def scenario(engine: VoisonaEngine) -> None:
        pass

    run(fake, scenario)

    expected = base64.b64encode(f"{USER}:{PASSWORD}".encode()).decode()
    assert fake.authorizations == {f"Basic {expected}"}


def test_synthesis_request_and_cleanup() -> None:
    fake = FakeVoisona()

    async def scenario(engine: VoisonaEngine) -> None:
        wav = await engine.synthesize("こんにちは", "田中傘", "Happy", {"speed": 1.5, "volume": 99})

        assert wav[:4] == b"RIFF"

    run(fake, scenario)

    assert fake.bodies == [
        {
            "language": "ja_JP",
            "voice_name": "tanaka-san_ja_JP",
            "destination": "memory",
            "force_enqueue": True,
            "text": "こんにちは",
            "global_parameters": {
                "speed": 1.5,
                "pitch": 0,
                "intonation": 1.0,
                "volume": 8,
                "style_weights": [0.0, 1.0, 0.0],
            },
        }
    ]
    assert fake.polls == 3
    assert fake.deleted == [UUID]


def test_long_text_is_split_and_joined() -> None:
    fake = FakeVoisona()
    fake.states = ["succeeded"]

    async def scenario(engine: VoisonaEngine) -> None:
        wav = await engine.synthesize("あ" * 400 + "。" + "い" * 400 + "。", "田中傘", "Normal", {})

        with wave.open(io.BytesIO(wav), "rb") as reader:
            assert reader.getnframes() == 2

    run(fake, scenario)

    assert all(len(body["text"]) <= 500 for body in fake.bodies)
    assert len(fake.deleted) == 2


def test_failed_state_raises_and_still_cleans_up() -> None:
    fake = FakeVoisona()
    fake.states = ["failed"]

    async def scenario(engine: VoisonaEngine) -> None:
        with pytest.raises(TTSError, match="失敗"):
            await engine.synthesize("a", "田中傘", "Normal", {})

    run(fake, scenario)

    assert fake.deleted == [UUID]


def test_http_error_message_does_not_contain_credentials() -> None:
    fake = FakeVoisona()
    fake.states = ["succeeded"]
    fake.wav_status = 500

    async def scenario(engine: VoisonaEngine) -> None:
        with pytest.raises(TTSError) as caught:
            await engine.synthesize("a", "田中傘", "Normal", {})

        expected = base64.b64encode(f"{USER}:{PASSWORD}".encode()).decode()
        assert expected not in str(caught.value)
        assert PASSWORD not in str(caught.value)
        assert "HTTP 500" in str(caught.value)

    run(fake, scenario)
