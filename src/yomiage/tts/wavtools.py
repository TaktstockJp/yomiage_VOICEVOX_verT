"""1回に合成できる文字数に上限があるエンジン向けの、文の分割と WAV の連結。"""

from __future__ import annotations

import io
import re
import wave
from collections.abc import Sequence

from .base import TTSError

_SENTENCE = re.compile(r".+?(?:[。！？!?、，,．]+|$)", re.DOTALL)


def split_text(text: str, limit: int) -> list[str]:
    """句読点の位置を優先して、limit 文字以下の断片に分割する。"""
    chunks: list[str] = []
    current = ""
    for sentence in _SENTENCE.findall(text):
        while len(sentence) > limit:
            if current:
                chunks.append(current)
                current = ""
            chunks.append(sentence[:limit])
            sentence = sentence[limit:]
        if len(current) + len(sentence) > limit:
            chunks.append(current)
            current = ""
        current += sentence
    if current:
        chunks.append(current)
    return chunks


def concat_wavs(parts: Sequence[bytes]) -> bytes:
    """同じ形式の WAV を順につなげる。"""
    if len(parts) == 1:
        return parts[0]

    output = io.BytesIO()
    try:
        with wave.open(output, "wb") as writer:
            for index, part in enumerate(parts):
                with wave.open(io.BytesIO(part), "rb") as reader:
                    if index == 0:
                        writer.setparams(reader.getparams())
                    writer.writeframes(reader.readframes(reader.getnframes()))
    except (wave.Error, EOFError) as error:
        raise TTSError(f"WAV の連結に失敗しました: {error}") from error
    return output.getvalue()
