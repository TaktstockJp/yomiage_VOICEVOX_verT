"""ギルドごとの読み上げの状態と、合成・再生のワーカー。"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

import discord

from ..tts.base import TTSError, VoiceParams, VoiceSelection
from ..tts.registry import EngineRegistry

_log = logging.getLogger(__name__)

_AUDIO_QUEUE_SIZE = 2

SourceFactory = Callable[[bytes], discord.AudioSource]
TextTarget = discord.TextChannel | discord.VoiceChannel | discord.StageChannel | discord.Thread


@dataclass(frozen=True)
class Utterance:
    """読み上げる1文。声はキューに入れた時点で確定させる。"""

    text: str
    voice: VoiceSelection
    params: VoiceParams


@dataclass(frozen=True)
class AudioClip:
    wav: bytes
    generation: int


def _clear(queue: asyncio.Queue[Any]) -> None:
    while not queue.empty():
        queue.get_nowait()


class ReadingSession:
    """合成ワーカーと再生ワーカーで、受け取った順に1文ずつ読み上げる。"""

    def __init__(
        self,
        voice_client: discord.VoiceClient,
        text_channel: TextTarget,
        registry: EngineRegistry,
        source_factory: SourceFactory,
    ) -> None:
        self.voice_client = voice_client
        self.text_channel = text_channel
        self._registry = registry
        self._source_factory = source_factory
        self._text_queue: asyncio.Queue[Utterance] = asyncio.Queue()
        self._audio_queue: asyncio.Queue[AudioClip] = asyncio.Queue(maxsize=_AUDIO_QUEUE_SIZE)
        # stop() のたびに進め、それより前に合成を始めた音声を再生しないようにする
        self._generation = 0
        self._tasks: list[asyncio.Task[None]] = []

    def start(self) -> None:
        self._tasks = [
            asyncio.create_task(self._synthesis_worker(), name="yomiage-synthesis"),
            asyncio.create_task(self._playback_worker(), name="yomiage-playback"),
        ]

    def enqueue(self, utterance: Utterance) -> None:
        self._text_queue.put_nowait(utterance)

    def stop(self) -> None:
        """再生中の音声と、待っている読み上げをすべて破棄する。"""
        self._generation += 1
        _clear(self._text_queue)
        _clear(self._audio_queue)
        self.voice_client.stop()

    async def close(self) -> None:
        for task in self._tasks:
            task.cancel()
        await asyncio.gather(*self._tasks, return_exceptions=True)
        self._tasks = []
        self.stop()

    async def _synthesis_worker(self) -> None:
        while True:
            utterance = await self._text_queue.get()
            generation = self._generation
            try:
                wav = await self._synthesize(utterance)
            except TTSError as error:
                _log.warning("音声合成に失敗しました: %s", error)
                continue
            except Exception:
                _log.exception("音声合成中に予期しないエラーが発生しました")
                continue
            if generation == self._generation:
                await self._audio_queue.put(AudioClip(wav, generation))

    async def _synthesize(self, utterance: Utterance) -> bytes:
        voice = utterance.voice
        engine = self._registry.get(voice.engine)
        if engine is None:
            raise TTSError(f"エンジンが登録されていません: {voice.engine}")
        return await engine.synthesize(utterance.text, voice.speaker, voice.style, utterance.params)

    async def _playback_worker(self) -> None:
        while True:
            clip = await self._audio_queue.get()
            # stop() の前に合成を終えて、キューの空きを待っていた音声はここで捨てる
            if clip.generation != self._generation:
                continue
            try:
                await self._play(clip)
            except Exception:
                _log.exception("音声の再生中にエラーが発生しました")

    async def _play(self, clip: AudioClip) -> None:
        loop = asyncio.get_running_loop()
        finished = asyncio.Event()

        def after(error: Exception | None) -> None:
            # 再生スレッドから呼ばれるので、イベントループ側で完了を伝える
            if error is not None:
                _log.warning("音声の再生に失敗しました: %s", error)
            loop.call_soon_threadsafe(finished.set)

        self.voice_client.play(self._source_factory(clip.wav), after=after)
        await finished.wait()
