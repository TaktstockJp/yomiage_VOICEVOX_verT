"""VC への参加と退出、読み上げの停止、メッセージの読み上げ。"""

from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING

import discord
from discord.ext import commands

from .. import __version__, messages
from ..reading.normalizer import incoming_from_discord, normalize, should_read

if TYPE_CHECKING:
    from ..app import YomiageBot

_log = logging.getLogger(__name__)


class VoiceCog(commands.Cog):
    def __init__(self, bot: YomiageBot) -> None:
        self.bot = bot

    @commands.hybrid_command(name="join", description="BOTをボイスチャンネルに呼ぶ")
    async def join(self, ctx: commands.Context[YomiageBot]) -> None:
        voice_state = ctx.author.voice
        if voice_state is None or voice_state.channel is None:
            await ctx.send(messages.NOT_IN_VOICE)
            return

        # 接続に3秒以上かかるとスラッシュコマンドが失敗扱いになるので、先に応答を保留する
        await ctx.defer()
        session = self.bot.sessions.get(ctx.guild.id)
        try:
            if session is None:
                voice_client = await voice_state.channel.connect()
                self.bot.open_session(voice_client, ctx.channel)
            else:
                await session.voice_client.move_to(voice_state.channel)
                session.text_channel = ctx.channel
        except (asyncio.TimeoutError, discord.ClientException) as error:
            _log.warning("ボイスチャンネルに接続できませんでした: %r", error)
            await ctx.send(messages.CONNECT_FAILED)
            return
        await ctx.send(messages.JOINED)

    @commands.hybrid_command(name="leave", description="BOTをボイスチャンネルから退出させる")
    async def leave(self, ctx: commands.Context[YomiageBot]) -> None:
        if ctx.guild.id not in self.bot.sessions:
            await ctx.send(messages.NOT_CONNECTED)
            return
        await ctx.defer()
        await self.bot.close_session(ctx.guild.id)
        await ctx.send(messages.LEFT)

    @commands.hybrid_command(name="stop", description="再生中の音声と、待っている読み上げをすべて止める")
    async def stop(self, ctx: commands.Context[YomiageBot]) -> None:
        session = self.bot.sessions.get(ctx.guild.id)
        if session is None:
            await ctx.send(messages.NOT_CONNECTED)
            return
        session.stop()
        await ctx.send(messages.STOPPED)

    @commands.hybrid_command(name="hello", description="バージョン情報を確認する")
    async def hello(self, ctx: commands.Context[YomiageBot]) -> None:
        await ctx.send(messages.version_info(__version__, self.bot.config.discord.command_prefix))

    @commands.hybrid_command(name="help", description="コマンドの一覧を表示する")
    async def help(self, ctx: commands.Context[YomiageBot]) -> None:
        await ctx.send(messages.help_text(self.bot.config.discord.command_prefix))

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        if message.guild is None or message.author.bot:
            return
        session = self.bot.sessions.get(message.guild.id)
        if session is None or message.channel.id != session.text_channel.id:
            return

        discord_config = self.bot.config.discord
        skip_prefixes = (
            discord_config.comment_prefix,
            discord_config.command_prefix,
            *discord_config.ignore_prefixes,
        )
        if not should_read(message.content, skip_prefixes):
            return

        storage = self.bot.storage
        lines = normalize(incoming_from_discord(message), storage.words(), storage.settings().max_chars)
        for line in lines:
            self.bot.speak(session, line, message.author.id)
