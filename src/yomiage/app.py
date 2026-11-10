"""Bot の生成、Cog の読み込み、エンジンの初期化、起動。"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

import aiohttp
import discord
from discord import app_commands
from discord.ext import commands

from . import messages
from .audio import FfmpegNotFoundError, create_source, find_ffmpeg
from .cogs.dictionary import DictionaryCog
from .cogs.notify import NotifyCog
from .cogs.settings import SettingsCog
from .cogs.speaker import SpeakerCog
from .cogs.voice import VoiceCog
from .config import Config, ConfigError, load_config
from .logs import setup_logging
from .reading.session import ReadingSession, TextTarget, Utterance
from .storage import Storage
from .tts.base import TTSEngine, VoiceSelection
from .tts.coeiroink import CoeiroinkEngine
from .tts.registry import EngineRegistry
from .tts.voicevox import VoicevoxEngine

_log = logging.getLogger(__name__)

_ERROR_WRAPPERS = (
    commands.HybridCommandError,
    commands.CommandInvokeError,
    app_commands.CommandInvokeError,
)


class NoEngineError(Exception):
    """利用できる TTS エンジンが1つもないことを表す例外。"""


def _guild_only(ctx: commands.Context[YomiageBot]) -> bool:
    if ctx.guild is None:
        raise commands.NoPrivateMessage()
    return True


def _intents() -> discord.Intents:
    intents = discord.Intents.none()
    intents.guilds = True
    intents.guild_messages = True
    intents.message_content = True
    intents.voice_states = True
    intents.members = True
    return intents


def _build_engines(config: Config, session: aiohttp.ClientSession) -> list[TTSEngine]:
    engines: list[TTSEngine] = [
        VoicevoxEngine(engine.name, engine.port, session) for engine in config.engines.voicevox
    ]
    if config.engines.coeiroink.enabled:
        engines.append(CoeiroinkEngine(config.engines.coeiroink.port, session))
    return engines


class YomiageBot(commands.Bot):
    def __init__(self, config: Config, database: Path | str, ffmpeg: str) -> None:
        super().__init__(
            command_prefix=config.discord.command_prefix,
            help_command=None,
            intents=_intents(),
            allowed_mentions=discord.AllowedMentions.none(),
            allowed_contexts=app_commands.AppCommandContext(guild=True, dm_channel=False, private_channel=False),
        )
        self.config = config
        self.storage = Storage(database)
        self.registry = EngineRegistry()
        self.sessions: dict[int, ReadingSession] = {}
        self._ffmpeg = ffmpeg
        self._tts_http: aiohttp.ClientSession | None = None
        self.add_check(_guild_only)

    async def setup_hook(self) -> None:
        self._tts_http = aiohttp.ClientSession()
        for engine in _build_engines(self.config, self._tts_http):
            await self.registry.add(engine)
        if not self.registry.engines():
            raise NoEngineError()
        await self.load_cogs()
        await self.tree.sync()

    async def load_cogs(self) -> None:
        for cog in (VoiceCog, SpeakerCog, DictionaryCog, SettingsCog, NotifyCog):
            await self.add_cog(cog(self))

    def open_session(self, voice_client: discord.VoiceClient, text_channel: TextTarget) -> ReadingSession:
        session = ReadingSession(
            voice_client,
            text_channel,
            self.registry,
            lambda wav: create_source(wav, self._ffmpeg),
        )
        session.start()
        self.sessions[voice_client.guild.id] = session
        return session

    async def close_session(self, guild_id: int) -> None:
        session = self.sessions.pop(guild_id, None)
        if session is None:
            return
        await session.close()
        if session.voice_client.is_connected():
            await session.voice_client.disconnect()

    def voice_for(self, user_id: int | None) -> VoiceSelection:
        """利用者の声を返す。使えない場合はデフォルトの声、それもなければ最初の声を返す。"""
        default = self.config.default_voice
        return self.registry.resolve(
            self.storage.user_voice(user_id) if user_id is not None else None,
            VoiceSelection(default.engine, default.speaker, default.style),
        )

    def speak(self, session: ReadingSession, text: str, user_id: int | None = None) -> None:
        voice = self.voice_for(user_id)
        session.enqueue(Utterance(text, voice, self.storage.style_params(voice)))

    async def on_ready(self) -> None:
        _log.info("%s としてログインしました", self.user)

    async def on_command_error(self, ctx: commands.Context[YomiageBot], error: Exception) -> None:
        while isinstance(error, _ERROR_WRAPPERS):
            error = error.original
        if isinstance(error, commands.CommandNotFound):
            return
        if isinstance(error, (commands.UserInputError, commands.CheckFailure, app_commands.TransformerError)):
            await ctx.send(messages.COMMAND_ERROR)
            return
        _log.error("コマンド %s の実行に失敗しました", ctx.command, exc_info=error)
        await ctx.send(messages.UNEXPECTED_ERROR)

    async def close(self) -> None:
        for guild_id in list(self.sessions):
            await self.close_session(guild_id)
        await self.registry.close_all()
        if self._tts_http is not None:
            await self._tts_http.close()
        await super().close()
        self.storage.close()


def _base_dir() -> Path:
    # PyInstaller でビルドした場合は exe の場所を基準にする
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path.cwd()


def main() -> int:
    base_dir = _base_dir()
    setup_logging(base_dir / "logs")
    try:
        config = load_config(base_dir / "config.toml")
        ffmpeg = find_ffmpeg(config.ffmpeg.path, base_dir)
    except (ConfigError, FfmpegNotFoundError) as error:
        _log.error("%s", error)
        return 1

    bot = YomiageBot(config, base_dir / "yomiage.db", ffmpeg)
    try:
        bot.run(config.discord.token, log_handler=None)
    except discord.PrivilegedIntentsRequired:
        _log.error("%s", messages.ERROR_PRIVILEGED_INTENTS)
        return 1
    except discord.LoginFailure:
        _log.error("%s", messages.ERROR_LOGIN)
        return 1
    except NoEngineError:
        _log.error("%s", messages.ERROR_NO_ENGINE)
        return 1
    return 0
