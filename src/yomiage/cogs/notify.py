"""入退室の通知、人数の表示、自動退出、時報。"""

from __future__ import annotations

import logging
from datetime import datetime, time
from typing import TYPE_CHECKING

import discord
from discord.ext import commands, tasks

from .. import messages
from ..reading.session import ReadingSession

if TYPE_CHECKING:
    from ..app import YomiageBot

_log = logging.getLogger(__name__)

_LOCAL_TIMEZONE = datetime.now().astimezone().tzinfo
_EVERY_HOUR = [time(hour=hour, tzinfo=_LOCAL_TIMEZONE) for hour in range(24)]


class NotifyCog(commands.Cog):
    def __init__(self, bot: YomiageBot) -> None:
        self.bot = bot

    async def cog_load(self) -> None:
        self.time_signal_loop.start()

    async def cog_unload(self) -> None:
        self.time_signal_loop.cancel()

    async def _announce(self, session: ReadingSession, text: str) -> None:
        """テキストチャンネルに投稿し、読み上げキューにも直接追加する。"""
        await session.text_channel.send(text)
        self.bot.speak(session, text)

    @commands.Cog.listener()
    async def on_voice_state_update(
        self,
        member: discord.Member,
        before: discord.VoiceState,
        after: discord.VoiceState,
    ) -> None:
        guild_id = member.guild.id
        session = self.bot.sessions.get(guild_id)
        if session is None:
            return

        if member.id == self.bot.user.id:
            if after.channel is None:
                await self.bot.close_session(guild_id)
            return

        if member.bot or before.channel == after.channel:
            return
        channel = session.voice_client.channel
        joined = after.channel == channel
        left = before.channel == channel
        if not (joined or left):
            return

        settings = self.bot.storage.settings()
        if settings.notify_join_leave:
            name = member.display_name
            await self._announce(session, messages.member_joined(name) if joined else messages.member_left(name))

        count = sum(1 for connected in channel.members if not connected.bot)
        if settings.report_member_count:
            await session.text_channel.send(messages.member_count(count))
        if left and count == 0 and settings.auto_leave:
            await session.text_channel.send(messages.LEAVING_ALONE)
            await self.bot.close_session(guild_id)

    @tasks.loop(time=_EVERY_HOUR)
    async def time_signal_loop(self) -> None:
        if not self.bot.storage.settings().time_signal:
            return
        text = messages.TIME_SIGNALS[datetime.now(_LOCAL_TIMEZONE).hour]
        for session in list(self.bot.sessions.values()):
            try:
                await self._announce(session, text)
            except discord.HTTPException:
                # 例外が外に出ると tasks.loop が止まり、以降の時報も鳴らなくなる
                _log.exception("時報の投稿に失敗しました")
