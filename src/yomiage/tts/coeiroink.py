"""COEIROINK v2 のエンジン。"""

from __future__ import annotations

import aiohttp

from .base import Speaker, Style, TTSEngine, TTSError, VoiceParams
from .http import request_bytes, request_json
from .voicevox import VOICEVOX_PARAM_SPECS


class CoeiroinkEngine(TTSEngine):
    param_specs = VOICEVOX_PARAM_SPECS

    def __init__(self, port: int, session: aiohttp.ClientSession, name: str = "COEIROINK") -> None:
        super().__init__(name)
        self._base_url = f"http://127.0.0.1:{port}"
        self._session = session

    async def reload(self) -> None:
        data = await request_json(self._session, "GET", f"{self._base_url}/v1/speakers")
        try:
            self._speakers = tuple(
                Speaker(
                    name=speaker["speakerName"],
                    id=speaker["speakerUuid"],
                    styles=tuple(Style(style["styleName"], style["styleId"]) for style in speaker["styles"]),
                )
                for speaker in data
            )
        except (KeyError, TypeError) as error:
            raise TTSError(f"{self.name} の話者一覧の形式が想定と異なります: {error!r}") from error

    async def synthesize(self, text: str, speaker: str, style: str, params: VoiceParams) -> bytes:
        found_speaker, found_style = self.find_style(speaker, style)
        values = self.resolve_params(params)
        return await request_bytes(
            self._session,
            "POST",
            f"{self._base_url}/v1/synthesis",
            json={
                "speakerUuid": found_speaker.id,
                "styleId": found_style.id,
                "text": text,
                "speedScale": values["speed"],
                "volumeScale": values["volume"],
                "pitchScale": values["pitch"],
                "intonationScale": values["intonation"],
                "prePhonemeLength": 0.0,
                "postPhonemeLength": 0.0,
                "outputSamplingRate": 44100,
            },
        )
