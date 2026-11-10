"""Voicepeak のコマンドラインを呼び出すエンジン。"""

from __future__ import annotations

import asyncio
import tempfile
from pathlib import Path

from .base import ParamSpec, Speaker, Style, TTSEngine, TTSError, VoiceParams
from .wavtools import concat_wavs, split_text

_MAX_CHARS = 140
_TIMEOUT_SECONDS = 60
_STANDARD_STYLE = Style("標準", "")
_EMOTION_VALUE = 100


class VoicepeakEngine(TTSEngine):
    param_specs = {
        "speed": ParamSpec(50, 200, 100),
        "pitch": ParamSpec(-300, 300, 0),
    }

    def __init__(self, executable: Path, name: str = "Voicepeak") -> None:
        super().__init__(name)
        self._executable = executable
        # Voicepeak は同時に実行できないので、すべての呼び出しを1件ずつにする
        self._lock = asyncio.Lock()

    async def _run(self, *args: str) -> str:
        try:
            process = await asyncio.create_subprocess_exec(
                str(self._executable),
                *args,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
        except OSError as error:
            raise TTSError(f"{self.name} を実行できません: {error}") from error

        try:
            stdout, _ = await asyncio.wait_for(process.communicate(), _TIMEOUT_SECONDS)
        except asyncio.TimeoutError as error:
            raise TTSError(f"{self.name} の実行がタイムアウトしました") from error
        finally:
            if process.returncode is None:
                process.kill()
                await process.wait()

        if process.returncode != 0:
            raise TTSError(f"{self.name} が終了コード {process.returncode} で終了しました")
        return stdout.decode("utf-8", errors="replace")

    async def _list(self, *args: str) -> list[str]:
        output = await self._run(*args)
        return [stripped for line in output.splitlines() if (stripped := line.strip())]

    async def reload(self) -> None:
        async with self._lock:
            speakers = []
            for narrator in await self._list("--list-narrator"):
                emotions = await self._list("--list-emotion", narrator)
                styles = (_STANDARD_STYLE, *(Style(emotion, emotion) for emotion in emotions))
                speakers.append(Speaker(name=narrator, styles=styles))
        self._speakers = tuple(speakers)

    async def synthesize(self, text: str, speaker: str, style: str, params: VoiceParams) -> bytes:
        _, found = self.find_style(speaker, style)
        values = self.resolve_params(params)
        arguments = ["-n", speaker, "--speed", str(round(values["speed"])), "--pitch", str(round(values["pitch"]))]
        if found.id:
            arguments += ["-e", f"{found.id}={_EMOTION_VALUE}"]

        parts = []
        async with self._lock:
            with tempfile.TemporaryDirectory(prefix="yomiage-") as directory:
                for index, chunk in enumerate(split_text(text, _MAX_CHARS)):
                    path = Path(directory) / f"voice{index}.wav"
                    # 「-」で始まる文がオプションと解釈されないよう、値を = でつなげて渡す
                    await self._run(f"--say={chunk}", "-o", str(path), *arguments)
                    if not path.is_file():
                        raise TTSError(f"{self.name} が音声ファイルを出力しませんでした")
                    parts.append(path.read_bytes())
        return concat_wavs(parts)
