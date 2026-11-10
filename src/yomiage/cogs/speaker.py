"""話者の変更、スタイルごとの調整、話者一覧。"""

from __future__ import annotations

import io
from collections.abc import Iterable, Sequence
from typing import TYPE_CHECKING

import discord
from discord import app_commands
from discord.ext import commands

from .. import messages
from ..tts.base import TTSEngine, VoiceSelection

if TYPE_CHECKING:
    from ..app import YomiageBot

_MESSAGE_LIMIT = 2000
_CHOICE_LIMIT = 25
_CHOICE_LENGTH = 100
_CODE_FENCE_LENGTH = len("```\n\n```")


def format_speakers(engines: Iterable[TTSEngine]) -> str:
    sections = []
    for engine in engines:
        lines = [f"【{engine.name}】"]
        lines += [
            f"{speaker.name}: {', '.join(style.name for style in speaker.styles)}"
            for speaker in engine.speakers()
        ]
        sections.append("\n".join(lines))
    return "\n\n".join(sections)


def build_choices(values: Iterable[str], current: str) -> list[app_commands.Choice[str]]:
    """入力中の文字を含む候補を、重複を除いて Discord の上限まで返す。"""
    needle = current.casefold()
    matches = [value for value in dict.fromkeys(values) if needle in value.casefold()]
    return [
        app_commands.Choice(name=value[:_CHOICE_LENGTH], value=value[:_CHOICE_LENGTH])
        for value in matches[:_CHOICE_LIMIT]
    ]


class SpeakerCog(commands.Cog):
    def __init__(self, bot: YomiageBot) -> None:
        self.bot = bot

    def _hint(self) -> str:
        return messages.show_speakers_hint(self.bot.config.discord.command_prefix)

    @commands.hybrid_command(name="chg_my_voice", description="自分の声を変更する")
    @app_commands.describe(speaker="話者", style="スタイル", engine="ソフト（省略できます）")
    async def chg_my_voice(
        self,
        ctx: commands.Context[YomiageBot],
        speaker: str,
        style: str,
        engine: str | None = None,
    ) -> None:
        registry = self.bot.registry
        if engine is not None and registry.get(engine) is None:
            await ctx.send(f"{messages.ENGINE_NOT_FOUND}\n{self._hint()}")
            return
        voice = registry.find(speaker, style, engine)
        if voice is None:
            await ctx.send(f"{messages.VOICE_NOT_FOUND}\n{self._hint()}")
            return
        self.bot.storage.set_user_voice(ctx.author.id, voice)
        await ctx.send(messages.VOICE_CHANGED)

    @commands.hybrid_command(name="chg_voice_setting", description="スタイルごとの話速などを変更する")
    @app_commands.describe(
        engine="ソフト",
        speaker="話者",
        style="スタイル",
        param="変更するパラメータ",
        value="変更後の値",
    )
    async def chg_voice_setting(
        self,
        ctx: commands.Context[YomiageBot],
        engine: str,
        speaker: str,
        style: str,
        param: str,
        value: float,
    ) -> None:
        target = self.bot.registry.get(engine)
        if target is None:
            await ctx.send(f"{messages.ENGINE_NOT_FOUND}\n{self._hint()}")
            return
        if not target.has_voice(speaker, style):
            await ctx.send(f"{messages.VOICE_NOT_FOUND}\n{self._hint()}")
            return
        spec = target.param_specs.get(param)
        if spec is None:
            await ctx.send(messages.param_not_found(list(target.param_specs)))
            return
        if not spec.contains(value):
            await ctx.send(messages.param_out_of_range(param, spec.min, spec.max))
            return

        voice = VoiceSelection(engine, speaker, style)
        if value == spec.default:
            self.bot.storage.delete_style_param(voice, param)
        else:
            self.bot.storage.set_style_param(voice, param, value)
        await ctx.send(messages.param_changed(param, value))

    @commands.hybrid_command(name="show_speakers", description="使えるソフトと話者とスタイルを確認する")
    async def show_speakers(self, ctx: commands.Context[YomiageBot]) -> None:
        text = format_speakers(self.bot.registry.engines())
        if len(text) + _CODE_FENCE_LENGTH <= _MESSAGE_LIMIT:
            await ctx.send(f"```\n{text}\n```")
            return
        data = io.BytesIO(text.encode("utf-8-sig"))
        await ctx.send(file=discord.File(data, filename="speakers.txt"))

    @commands.hybrid_command(name="reload", description="各ソフトから話者の一覧を取り直す")
    async def reload(self, ctx: commands.Context[YomiageBot]) -> None:
        await ctx.defer()
        failed = await self.bot.registry.reload_all()
        await ctx.send(messages.reload_failed(failed) if failed else messages.RELOADED)

    def _selected_engines(self, interaction: discord.Interaction) -> Sequence[TTSEngine]:
        selected = self.bot.registry.get(interaction.namespace.engine or "")
        return [selected] if selected else self.bot.registry.engines()

    @chg_my_voice.autocomplete("speaker")
    @chg_voice_setting.autocomplete("speaker")
    async def speaker_autocomplete(
        self, interaction: discord.Interaction, current: str
    ) -> list[app_commands.Choice[str]]:
        names = (s.name for engine in self._selected_engines(interaction) for s in engine.speakers())
        return build_choices(names, current)

    @chg_my_voice.autocomplete("style")
    @chg_voice_setting.autocomplete("style")
    async def style_autocomplete(
        self, interaction: discord.Interaction, current: str
    ) -> list[app_commands.Choice[str]]:
        names = (
            style.name
            for engine in self._selected_engines(interaction)
            for speaker in engine.speakers()
            if speaker.name == interaction.namespace.speaker
            for style in speaker.styles
        )
        return build_choices(names, current)

    @chg_my_voice.autocomplete("engine")
    @chg_voice_setting.autocomplete("engine")
    async def engine_autocomplete(
        self, interaction: discord.Interaction, current: str
    ) -> list[app_commands.Choice[str]]:
        return build_choices((engine.name for engine in self.bot.registry.engines()), current)

    @chg_voice_setting.autocomplete("param")
    async def param_autocomplete(
        self, interaction: discord.Interaction, current: str
    ) -> list[app_commands.Choice[str]]:
        names = (name for engine in self._selected_engines(interaction) for name in engine.param_specs)
        return build_choices(names, current)
