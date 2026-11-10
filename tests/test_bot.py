"""Discord に接続せずに確認できる、コマンド定義とイベント処理のテスト。"""

import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

from yomiage import messages
from yomiage.app import YomiageBot
from yomiage.cogs.dictionary import words_to_csv
from yomiage.cogs.notify import NotifyCog
from yomiage.cogs.settings import format_settings
from yomiage.cogs.speaker import build_choices, format_speakers
from yomiage.cogs.voice import VoiceCog
from yomiage.config import Config, DefaultVoiceConfig, DiscordConfig, EnginesConfig, FfmpegConfig
from yomiage.storage import Settings, Storage
from yomiage.tts.base import Speaker, Style

CONFIG = Config(DiscordConfig(token="x"), DefaultVoiceConfig(), FfmpegConfig(), EnginesConfig())


def commands_payload() -> dict:
    async def main() -> dict:
        bot = YomiageBot(CONFIG, ":memory:", "ffmpeg")
        try:
            await bot.load_cogs()
            return {command.name: command.to_dict(bot.tree) for command in bot.tree.get_commands()}
        finally:
            for name in list(bot.cogs):
                await bot.remove_cog(name)
            bot.storage.close()

    return asyncio.run(main())


def test_slash_commands_have_no_group_and_match_the_spec() -> None:
    assert set(commands_payload()) == {
        "join", "leave", "stop", "hello", "help",
        "wlist",
        "chg_my_voice", "chg_voice_setting", "show_speakers", "reload",
        "inform_someone_come", "number_of_people", "auto_leave", "time_signal",
        "word_count_limit", "show_setting",
    }  # fmt: skip


def test_slash_commands_are_guild_only() -> None:
    assert all(payload["contexts"] == [0] for payload in commands_payload().values())


def test_voice_arguments_have_autocomplete() -> None:
    options = {o["name"]: o for o in commands_payload()["chg_my_voice"]["options"]}

    assert all(options[name]["autocomplete"] for name in ("speaker", "style", "engine"))
    assert options["speaker"]["required"] is True
    assert options["engine"]["required"] is False


def test_wlist_has_subcommands() -> None:
    options = commands_payload()["wlist"]["options"]

    assert {option["name"] for option in options} == {"add", "delete", "show"}


def test_help_fits_in_one_message() -> None:
    assert len(messages.help_text("!")) <= 2000


def test_build_choices_filters_dedupes_and_limits() -> None:
    assert [c.value for c in build_choices(["Abc", "abd", "x", "Abc"], "AB")] == ["Abc", "abd"]
    assert len(build_choices([str(i) for i in range(50)], "")) == 25


def test_format_speakers() -> None:
    engine = SimpleNamespace(
        name="VOICEVOX",
        speakers=lambda: [Speaker("ずんだもん", (Style("ノーマル", 3), Style("あまあま", 1)))],
    )

    assert format_speakers([engine]) == "【VOICEVOX】\nずんだもん: ノーマル, あまあま"


def test_words_to_csv_is_excel_friendly() -> None:
    assert words_to_csv([("A,B", "えー")]) == '﻿"A,B",えー\r\n'.encode("utf-8")


def test_format_settings() -> None:
    text = format_settings(Settings(auto_leave=False, max_chars=80))

    assert "自動退出: オフ" in text
    assert "時報: オン" in text
    assert "文字数制限: 80" in text


class FakeBot:
    def __init__(self) -> None:
        self.storage = Storage(":memory:")
        self.sessions: dict[int, SimpleNamespace] = {}
        self.spoken: list[tuple[str, int | None]] = []
        self.close_session = AsyncMock()
        self.user = SimpleNamespace(id=999)
        self.config = CONFIG

    def speak(self, session: object, text: str, user_id: int | None = None) -> None:
        self.spoken.append((text, user_id))


GUILD_ID = 1
VC = SimpleNamespace(id=10, members=[])
OTHER_VC = SimpleNamespace(id=20, members=[])
TEXT_CHANNEL_ID = 100


@pytest.fixture
def bot():
    fake = FakeBot()
    fake.sessions[GUILD_ID] = SimpleNamespace(
        voice_client=SimpleNamespace(channel=VC),
        text_channel=SimpleNamespace(id=TEXT_CHANNEL_ID, send=AsyncMock()),
    )
    VC.members = []
    yield fake
    fake.storage.close()


def sent(bot: FakeBot) -> list[str]:
    return [call.args[0] for call in bot.sessions[GUILD_ID].text_channel.send.call_args_list]


def member(id: int = 1, is_bot: bool = False) -> SimpleNamespace:
    return SimpleNamespace(id=id, bot=is_bot, display_name="太郎", guild=SimpleNamespace(id=GUILD_ID))


def state(channel: object | None) -> SimpleNamespace:
    return SimpleNamespace(channel=channel)


def voice_update(bot: FakeBot, who: SimpleNamespace, before: object | None, after: object | None) -> None:
    asyncio.run(NotifyCog(bot).on_voice_state_update(who, state(before), state(after)))


def test_join_is_announced_read_and_counted(bot: FakeBot) -> None:
    VC.members = [member()]

    voice_update(bot, member(), None, VC)

    assert sent(bot) == ["太郎さんが入室したのだ", "現在1人接続しているのだ"]
    assert bot.spoken == [("太郎さんが入室したのだ", None)]


def test_last_member_leaving_makes_the_bot_leave(bot: FakeBot) -> None:
    voice_update(bot, member(), VC, None)

    assert sent(bot)[-1] == messages.LEAVING_ALONE
    bot.close_session.assert_awaited_once_with(GUILD_ID)


def test_auto_leave_can_be_disabled(bot: FakeBot) -> None:
    bot.storage.set_setting("auto_leave", False)

    voice_update(bot, member(), VC, None)

    bot.close_session.assert_not_awaited()


def test_auto_leave_works_with_notifications_off(bot: FakeBot) -> None:
    bot.storage.set_setting("notify_join_leave", False)
    bot.storage.set_setting("report_member_count", False)

    voice_update(bot, member(), VC, None)

    assert sent(bot) == [messages.LEAVING_ALONE]
    assert bot.spoken == []
    bot.close_session.assert_awaited_once_with(GUILD_ID)


def test_other_bots_are_not_counted(bot: FakeBot) -> None:
    VC.members = [member(id=2, is_bot=True)]

    voice_update(bot, member(), VC, None)

    assert "現在0人接続しているのだ" in sent(bot)
    bot.close_session.assert_awaited_once()


def test_bot_members_and_other_channels_are_ignored(bot: FakeBot) -> None:
    voice_update(bot, member(id=2, is_bot=True), None, VC)
    voice_update(bot, member(), None, OTHER_VC)
    voice_update(bot, member(), VC, VC)

    assert sent(bot) == []
    assert bot.spoken == []


def test_session_is_closed_when_the_bot_is_disconnected_externally(bot: FakeBot) -> None:
    voice_update(bot, member(id=999, is_bot=True), VC, None)

    bot.close_session.assert_awaited_once_with(GUILD_ID)
    assert sent(bot) == []


def test_nothing_happens_without_a_session() -> None:
    fake = FakeBot()

    voice_update(fake, member(), None, VC)

    assert fake.spoken == []
    fake.storage.close()


def message(content: str = "こんにちは", channel_id: int = TEXT_CHANNEL_ID, is_bot: bool = False) -> MagicMock:
    return MagicMock(
        content=content,
        guild=SimpleNamespace(id=GUILD_ID),
        channel=SimpleNamespace(id=channel_id),
        author=SimpleNamespace(id=5, bot=is_bot),
        stickers=[],
        attachments=[],
        mentions=[],
        role_mentions=[],
        channel_mentions=[],
    )


def receive(bot: FakeBot, incoming: MagicMock) -> None:
    asyncio.run(VoiceCog(bot).on_message(incoming))


def test_message_is_read_with_the_authors_voice(bot: FakeBot) -> None:
    receive(bot, message("一行目\n二行目"))

    assert bot.spoken == [("一行目", 5), ("二行目", 5)]


@pytest.mark.parametrize("content", [">コメント", "$他", "?他", "!join"])
def test_prefixed_messages_are_not_read(bot: FakeBot, content: str) -> None:
    receive(bot, message(content))

    assert bot.spoken == []


def test_other_channels_and_bots_are_not_read(bot: FakeBot) -> None:
    receive(bot, message(channel_id=TEXT_CHANNEL_ID + 1))
    receive(bot, message(is_bot=True))

    assert bot.spoken == []


def test_dictionary_and_limit_are_applied(bot: FakeBot) -> None:
    bot.storage.set_word("朝", "あさ")
    bot.storage.set_setting("max_chars", 3)

    receive(bot, message("朝ごはんです"))

    assert bot.spoken == [("あさご以下略", 5)]
