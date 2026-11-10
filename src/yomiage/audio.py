"""WAV のバイト列を Discord で再生できる音声ソースに変換する。"""

from __future__ import annotations

import io
import shutil
from pathlib import Path

import discord


class FfmpegNotFoundError(Exception):
    """FFmpeg の実行ファイルが見つからないことを表す例外。"""


def find_ffmpeg(configured_path: str, base_dir: Path) -> str:
    """設定のパス、同梱の ffmpeg/ffmpeg.exe、PATH の順に FFmpeg を探す。"""
    if configured_path:
        if Path(configured_path).is_file():
            return configured_path
        raise FfmpegNotFoundError(f"設定された FFmpeg が見つかりません: {configured_path}")

    bundled = base_dir / "ffmpeg" / "ffmpeg.exe"
    if bundled.is_file():
        return str(bundled)

    found = shutil.which("ffmpeg")
    if found:
        return found
    raise FfmpegNotFoundError("FFmpeg が見つかりません。config.toml の [ffmpeg] の path を指定してください。")


def create_source(wav: bytes, ffmpeg: str) -> discord.AudioSource:
    return discord.FFmpegOpusAudio(
        io.BytesIO(wav),
        pipe=True,
        executable=ffmpeg,
        options="-loglevel error",
    )
