"""Discord のメッセージを、読み上げる文の並びに変換する。"""

from __future__ import annotations

import re
from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from .. import messages

if TYPE_CHECKING:
    import discord

_CODE_BLOCK = re.compile(r"```.*?```", re.DOTALL)
_INLINE_CODE = re.compile(r"`[^`]+`")
_SPOILER = re.compile(r"\|\|.+?\|\|", re.DOTALL)
# 「https://example.comだよ」の「だよ」まで URL に含めないよう、URL に使える ASCII 文字に限る
_URL = re.compile(r"<https?://[^\s>]+>|https?://[A-Za-z0-9\-._~:/?#\[\]@!$&'()*+,;=%]+")
_USER_MENTION = re.compile(r"<@!?(\d+)>")
_ROLE_MENTION = re.compile(r"<@&(\d+)>")
_CHANNEL_MENTION = re.compile(r"<#(\d+)>")
_CUSTOM_EMOJI = re.compile(r"<a?:(\w+):\d+>")


@dataclass(frozen=True)
class IncomingMessage:
    """読み上げに必要な情報だけを取り出したメッセージ。"""

    content: str
    stickers: tuple[str, ...] = ()
    attachments: tuple[str, ...] = ()
    users: Mapping[int, str] = field(default_factory=dict)
    roles: Mapping[int, str] = field(default_factory=dict)
    channels: Mapping[int, str] = field(default_factory=dict)


def incoming_from_discord(message: discord.Message) -> IncomingMessage:
    return IncomingMessage(
        content=message.content,
        stickers=tuple(sticker.name for sticker in message.stickers),
        attachments=tuple(attachment.filename for attachment in message.attachments),
        users={user.id: user.display_name for user in message.mentions},
        roles={role.id: role.name for role in message.role_mentions},
        channels={channel.id: channel.name for channel in message.channel_mentions},
    )


def should_read(content: str, skip_prefixes: Iterable[str]) -> bool:
    """コメントや Bot のコマンドなど、読まない記号で始まっていなければ True を返す。"""
    return not content.startswith(tuple(skip_prefixes))


def _replace_code(text: str, message: IncomingMessage) -> str:
    text = _CODE_BLOCK.sub(messages.CODE_BLOCK, text)
    return _INLINE_CODE.sub(messages.CODE_BLOCK, text)


def _replace_spoilers(text: str, message: IncomingMessage) -> str:
    return _SPOILER.sub(messages.SPOILER, text)


def _replace_urls(text: str, message: IncomingMessage) -> str:
    return _URL.sub(messages.URL, text)


def _replace_mentions(text: str, message: IncomingMessage) -> str:
    def resolver(names: Mapping[int, str]) -> Callable[[re.Match[str]], str]:
        return lambda match: names.get(int(match[1]), "")

    text = _USER_MENTION.sub(resolver(message.users), text)
    text = _ROLE_MENTION.sub(resolver(message.roles), text)
    return _CHANNEL_MENTION.sub(resolver(message.channels), text)


def _replace_custom_emoji(text: str, message: IncomingMessage) -> str:
    return _CUSTOM_EMOJI.sub(r"\1", text)


# コードブロックの中身を他の規則で書き換えないよう、コードの置換を最初に行う
_TEXT_STEPS = (
    _replace_code,
    _replace_spoilers,
    _replace_urls,
    _replace_mentions,
    _replace_custom_emoji,
)


def _apply_dictionary(text: str, words: Sequence[tuple[str, str]]) -> str:
    # 1回の走査で置換し、置換後の読みが別の単語としてさらに置換されないようにする
    readings = {word: reading for word, reading in words if word}
    if not readings:
        return text
    pattern = "|".join(re.escape(word) for word in sorted(readings, key=len, reverse=True))
    return re.sub(pattern, lambda match: readings[match[0]], text)


def _limit_length(text: str, max_chars: int) -> str:
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + messages.OMITTED


def _attachment_kinds(filenames: Iterable[str]) -> list[str]:
    """添付ファイルの種類を、重複を除いて出現順に返す。"""
    kinds: dict[str, None] = {}
    for filename in filenames:
        extension = "." + filename.rpartition(".")[2].lower()
        kinds[messages.ATTACHMENT_KINDS.get(extension, messages.DEFAULT_ATTACHMENT_KIND)] = None
    return list(kinds)


def normalize(
    message: IncomingMessage,
    words: Sequence[tuple[str, str]],
    max_chars: int,
) -> list[str]:
    """メッセージを、読み上げキューに入れる順の文のリストに変換する。"""
    text = message.content
    for step in _TEXT_STEPS:
        text = step(text, message)

    text = "\n".join(part for part in (text, *message.stickers) if part)
    text = _apply_dictionary(text, words)
    text = _limit_length(text, max_chars)
    lines = [stripped for line in text.splitlines() if (stripped := line.strip())]

    kinds = _attachment_kinds(message.attachments)
    if lines:
        return lines + [messages.attachment_suffix(kind) for kind in kinds]
    return [messages.attachment_only(kind) for kind in kinds]
