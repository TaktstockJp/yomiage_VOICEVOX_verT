import io
import wave

import pytest

from yomiage.tts.base import TTSError
from yomiage.tts.wavtools import concat_wavs, split_text


def make_wav(frames: bytes, rate: int = 24000) -> bytes:
    output = io.BytesIO()
    with wave.open(output, "wb") as writer:
        writer.setnchannels(1)
        writer.setsampwidth(2)
        writer.setframerate(rate)
        writer.writeframes(frames)
    return output.getvalue()


def test_short_text_is_not_split() -> None:
    assert split_text("こんにちは。", 140) == ["こんにちは。"]


def test_text_is_split_at_punctuation() -> None:
    assert split_text("あいう。かきく。さしす。", 8) == ["あいう。かきく。", "さしす。"]


def test_text_without_punctuation_is_cut_at_the_limit() -> None:
    assert split_text("あいうえおかきくけ", 4) == ["あいうえ", "おかきく", "け"]


def test_long_sentence_after_short_one() -> None:
    assert split_text("あ。いうえおかきくけ", 4) == ["あ。", "いうえお", "かきくけ"]


def test_every_chunk_respects_the_limit_and_no_text_is_lost() -> None:
    text = "吾輩は猫である。名前はまだ無い！どこで生れたか、とんと見当がつかぬ？" * 20

    chunks = split_text(text, 140)

    assert all(len(chunk) <= 140 for chunk in chunks)
    assert "".join(chunks) == text


def test_concat_joins_frames() -> None:
    joined = concat_wavs([make_wav(b"\x01\x00"), make_wav(b"\x02\x00\x03\x00")])

    with wave.open(io.BytesIO(joined), "rb") as reader:
        assert reader.getframerate() == 24000
        assert reader.readframes(reader.getnframes()) == b"\x01\x00\x02\x00\x03\x00"


def test_single_part_is_returned_as_is() -> None:
    assert concat_wavs([b"not parsed"]) == b"not parsed"


def test_invalid_wav_becomes_tts_error() -> None:
    with pytest.raises(TTSError):
        concat_wavs([b"bad", b"bad"])
