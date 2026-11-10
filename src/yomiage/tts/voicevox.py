"""VOICEVOX および同じ API を持つソフトのエンジン。"""

from __future__ import annotations

from collections.abc import Mapping

import aiohttp

from .base import ParamSpec, Speaker, Style, TTSEngine, TTSError, VoiceParams
from .http import request_bytes, request_json

VOICEVOX_PARAM_SPECS: Mapping[str, ParamSpec] = {
    "speed": ParamSpec(0.5, 2.0, 1.2),
    "pitch": ParamSpec(-0.15, 0.15, 0.0),
    "intonation": ParamSpec(0.0, 2.0, 1.0),
    "volume": ParamSpec(0.0, 2.0, 1.0),
}


class VoicevoxEngine(TTSEngine):
    param_specs = VOICEVOX_PARAM_SPECS

    def __init__(self, name: str, port: int, session: aiohttp.ClientSession) -> None:
        super().__init__(name)
        self._base_url = f"http://127.0.0.1:{port}"
        self._session = session

    async def reload(self) -> None:
        data = await request_json(self._session, "GET", f"{self._base_url}/speakers")
        try:
            self._speakers = tuple(
                Speaker(
                    name=speaker["name"],
                    styles=tuple(Style(style["name"], style["id"]) for style in speaker["styles"]),
                )
                for speaker in data
            )
        except (KeyError, TypeError) as error:
            raise TTSError(f"{self.name} の話者一覧の形式が想定と異なります: {error!r}") from error

    async def synthesize(self, text: str, speaker: str, style: str, params: VoiceParams) -> bytes:
        _, found = self.find_style(speaker, style)
        values = self.resolve_params(params)
        query = await request_json(
            self._session,
            "POST",
            f"{self._base_url}/audio_query",
            params={"text": text, "speaker": found.id},
        )
        query.update(
            speedScale=values["speed"],
            pitchScale=values["pitch"],
            intonationScale=values["intonation"],
            volumeScale=values["volume"],
        )
        return await request_bytes(
            self._session,
            "POST",
            f"{self._base_url}/synthesis",
            params={"speaker": found.id},
            json=query,
        )
