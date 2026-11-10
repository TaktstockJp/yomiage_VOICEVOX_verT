"""VoiSona Talk の REST API を呼び出すエンジン。"""

from __future__ import annotations

import asyncio
import base64
import contextlib
from typing import Any
from urllib.parse import quote

import aiohttp

from .base import ParamSpec, Speaker, Style, TTSEngine, TTSError, VoiceParams
from .http import request_bytes, request_json
from .wavtools import concat_wavs, split_text

_LANGUAGE = "ja_JP"
_MAX_CHARS = 500
_TIMEOUT_SECONDS = 60
_POLL_INITIAL_SECONDS = 0.05
_POLL_MAX_SECONDS = 0.5


def _display_name(voice: dict[str, Any]) -> str:
    for entry in voice.get("display_names", []):
        if entry["language"] == _LANGUAGE:
            return entry["name"]
    return voice["voice_name"]


class VoisonaEngine(TTSEngine):
    param_specs = {
        "speed": ParamSpec(0.2, 5.0, 1.0),
        "pitch": ParamSpec(-600, 600, 0),
        "intonation": ParamSpec(0.0, 2.0, 1.0),
        "volume": ParamSpec(-8, 8, 0),
    }

    def __init__(
        self,
        port: int,
        user: str,
        password: str,
        session: aiohttp.ClientSession,
        name: str = "VoiSona Talk",
    ) -> None:
        super().__init__(name)
        self._base_url = f"http://127.0.0.1:{port}/api/talk/v1"
        self._session = session
        credentials = base64.b64encode(f"{user}:{password}".encode()).decode()
        self._headers = {"Authorization": f"Basic {credentials}"}

    async def _json(self, method: str, path: str, **kwargs: Any) -> Any:
        return await request_json(self._session, method, f"{self._base_url}{path}", headers=self._headers, **kwargs)

    async def reload(self) -> None:
        data = await self._json("GET", "/voices")
        speakers: dict[str, Speaker] = {}
        try:
            for voice in data["items"]:
                voice_name = voice["voice_name"]
                # 同じボイスの別バージョンは1つにまとめる。合成時はバージョンを指定しない
                if _LANGUAGE not in voice["languages"] or voice_name in speakers:
                    continue
                detail = await self._json("GET", f"/voices/{quote(voice_name)}/{quote(voice['voice_version'])}")
                speakers[voice_name] = Speaker(
                    name=_display_name(voice),
                    id=voice_name,
                    styles=tuple(Style(name, index) for index, name in enumerate(detail["style_names"])),
                )
        except (KeyError, TypeError) as error:
            raise TTSError(f"{self.name} の話者一覧の形式が想定と異なります: {error!r}") from error
        self._speakers = tuple(speakers.values())

    async def synthesize(self, text: str, speaker: str, style: str, params: VoiceParams) -> bytes:
        found_speaker, found_style = self.find_style(speaker, style)
        body = {
            "language": _LANGUAGE,
            "voice_name": found_speaker.id,
            "destination": "memory",
            "force_enqueue": True,
            "global_parameters": {
                **self.resolve_params(params),
                "style_weights": [float(s.id == found_style.id) for s in found_speaker.styles],
            },
        }
        return concat_wavs([await self._synthesize_chunk(chunk, body) for chunk in split_text(text, _MAX_CHARS)])

    async def _synthesize_chunk(self, text: str, body: dict[str, Any]) -> bytes:
        created = await self._json("POST", "/speech-syntheses", json={**body, "text": text})
        try:
            path = f"/speech-syntheses/{created['uuid']}"
        except (KeyError, TypeError) as error:
            raise TTSError(f"{self.name} の応答の形式が想定と異なります: {error!r}") from error

        try:
            await self._wait_until_finished(path)
            return await request_bytes(self._session, "GET", f"{self._base_url}{path}/wav", headers=self._headers)
        finally:
            # 合成結果は VoiSona のメモリに残り続けるので、取得後に消す
            with contextlib.suppress(TTSError):
                await self._json("DELETE", path)

    async def _wait_until_finished(self, path: str) -> None:
        # VoiSona には完了の通知がないため、状態を問い合わせて待つ
        loop = asyncio.get_running_loop()
        deadline = loop.time() + _TIMEOUT_SECONDS
        delay = _POLL_INITIAL_SECONDS
        while True:
            info = await self._json("GET", path)
            state = info.get("state") if isinstance(info, dict) else None
            if state == "succeeded":
                return
            if state == "failed":
                raise TTSError(f"{self.name} が音声合成に失敗しました")
            if loop.time() >= deadline:
                raise TTSError(f"{self.name} の音声合成がタイムアウトしました")
            await asyncio.sleep(delay)
            delay = min(delay * 1.5, _POLL_MAX_SECONDS)
