"""設定の切り替えと確認。"""

from __future__ import annotations

from dataclasses import asdict
from typing import TYPE_CHECKING

from discord import app_commands
from discord.ext import commands

from .. import messages
from ..storage import Settings

if TYPE_CHECKING:
    from ..app import YomiageBot


def format_settings(settings: Settings) -> str:
    lines = []
    for key, value in asdict(settings).items():
        shown = messages.BOOL_LABELS[value] if isinstance(value, bool) else value
        lines.append(f"{messages.SETTING_LABELS[key]}: {shown}")
    return "```\n" + "\n".join(lines) + "\n```"


class SettingsCog(commands.Cog):
    def __init__(self, bot: YomiageBot) -> None:
        self.bot = bot

    async def _toggle(self, ctx: commands.Context[YomiageBot], key: str) -> None:
        enabled = not getattr(self.bot.storage.settings(), key)
        self.bot.storage.set_setting(key, enabled)
        await ctx.send(messages.setting_changed(messages.SETTING_LABELS[key], enabled))

    @commands.hybrid_command(name="inform_someone_come", description="入退出の通知のオンオフを切り替える")
    async def inform_someone_come(self, ctx: commands.Context[YomiageBot]) -> None:
        await self._toggle(ctx, "notify_join_leave")

    @commands.hybrid_command(name="number_of_people", description="在室人数チェックのオンオフを切り替える")
    async def number_of_people(self, ctx: commands.Context[YomiageBot]) -> None:
        await self._toggle(ctx, "report_member_count")

    @commands.hybrid_command(name="auto_leave", description="自動退出のオンオフを切り替える")
    async def auto_leave(self, ctx: commands.Context[YomiageBot]) -> None:
        await self._toggle(ctx, "auto_leave")

    @commands.hybrid_command(name="time_signal", description="時報のオンオフを切り替える")
    async def time_signal(self, ctx: commands.Context[YomiageBot]) -> None:
        await self._toggle(ctx, "time_signal")

    @commands.hybrid_command(name="word_count_limit", description="読み上げる文字数の上限を設定する")
    @app_commands.describe(limit="文字数の上限")
    async def word_count_limit(
        self,
        ctx: commands.Context[YomiageBot],
        limit: commands.Range[int, 1, 2000],
    ) -> None:
        self.bot.storage.set_setting("max_chars", limit)
        await ctx.send(messages.word_limit_changed(limit))

    @commands.hybrid_command(name="show_setting", description="現在の設定を確認する")
    async def show_setting(self, ctx: commands.Context[YomiageBot]) -> None:
        await ctx.send(format_settings(self.bot.storage.settings()))
