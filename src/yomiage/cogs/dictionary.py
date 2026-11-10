"""単語帳のコマンド。"""

from __future__ import annotations

import csv
import io
from collections.abc import Iterable
from typing import TYPE_CHECKING

import discord
from discord import app_commands
from discord.ext import commands

from .. import messages

if TYPE_CHECKING:
    from ..app import YomiageBot


def words_to_csv(words: Iterable[tuple[str, str]]) -> bytes:
    buffer = io.StringIO(newline="")
    csv.writer(buffer).writerows(words)
    # Excel で文字化けしないよう BOM を付ける
    return buffer.getvalue().encode("utf-8-sig")


class DictionaryCog(commands.Cog):
    def __init__(self, bot: YomiageBot) -> None:
        self.bot = bot

    @commands.hybrid_group(name="wlist", description="単語帳を操作する", invoke_without_command=True)
    async def wlist(self, ctx: commands.Context[YomiageBot]) -> None:
        await ctx.send(messages.COMMAND_ERROR)

    @wlist.command(name="add", description="単語の読みを登録する")
    @app_commands.describe(word="単語", reading="読み")
    async def add(self, ctx: commands.Context[YomiageBot], word: str, reading: str) -> None:
        self.bot.storage.set_word(word, reading)
        await ctx.send(messages.word_added(word, reading))

    @wlist.command(name="delete", description="単語の登録を消す")
    @app_commands.describe(word="単語")
    async def delete(self, ctx: commands.Context[YomiageBot], word: str) -> None:
        deleted = self.bot.storage.delete_word(word)
        await ctx.send(messages.word_deleted(word) if deleted else messages.WORD_NOT_FOUND)

    @wlist.command(name="show", description="登録内容をCSVファイルで確認する")
    async def show(self, ctx: commands.Context[YomiageBot]) -> None:
        data = io.BytesIO(words_to_csv(self.bot.storage.words()))
        await ctx.send(file=discord.File(data, filename="wordlist.csv"))
