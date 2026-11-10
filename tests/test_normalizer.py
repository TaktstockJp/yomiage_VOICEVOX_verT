from types import SimpleNamespace

import pytest

from yomiage.reading.normalizer import (
    IncomingMessage,
    incoming_from_discord,
    normalize,
    should_read,
)


def read(content: str = "", words=(), max_chars: int = 200, **fields) -> list[str]:
    return normalize(IncomingMessage(content, **fields), words, max_chars)


@pytest.mark.parametrize(
    ("content", "expected"),
    [
        (">コメント", False),
        ("$他のBot", False),
        ("?他のBot", False),
        ("!join", False),
        ("普通の発言", True),
        ("文中の>は読む", True),
        ("", True),
    ],
)
def test_should_read(content: str, expected: bool) -> None:
    assert should_read(content, [">", "$", "?", "!"]) is expected


def test_plain_text_is_read_as_is() -> None:
    assert read("こんにちは") == ["こんにちは"]


def test_each_line_becomes_one_utterance_and_blank_lines_are_dropped() -> None:
    assert read("一行目\n\n  \n二行目") == ["一行目", "二行目"]


@pytest.mark.parametrize(
    ("content", "expected"),
    [
        ("前```\nprint('`')\n```後", "前コードブロック後"),
        ("```a``` と ```b```", "コードブロック と コードブロック"),
        ("`x = 1` です", "コードブロック です"),
    ],
)
def test_code_is_replaced(content: str, expected: str) -> None:
    assert read(content) == [expected]


def test_code_contents_are_not_processed_by_other_rules() -> None:
    assert read("`https://example.com <@1>`", users={1: "太郎"}) == ["コードブロック"]


@pytest.mark.parametrize(
    ("content", "expected"),
    [
        ("||秘密|の話|| です", "ネタバレ防止 です"),
        ("||a|| と ||b||", "ネタバレ防止 と ネタバレ防止"),
        ("||改行\nあり||", "ネタバレ防止"),
    ],
)
def test_spoilers_are_replaced(content: str, expected: str) -> None:
    assert read(content) == [expected]


@pytest.mark.parametrize(
    ("content", "expected"),
    [
        ("https://example.com/a?b=c#d", "URL"),
        ("http://example.com を見て", "URL を見て"),
        ("<https://example.com/a>", "URL"),
        ("https://example.comだよ", "URLだよ"),
    ],
)
def test_urls_are_replaced(content: str, expected: str) -> None:
    assert read(content) == [expected]


def test_mentions_use_resolved_names() -> None:
    result = read(
        "<@1> <@!2> <@&3> <#4>",
        users={1: "太郎", 2: "花子"},
        roles={3: "管理者"},
        channels={4: "雑談"},
    )

    assert result == ["太郎 花子 管理者 雑談"]


def test_unresolved_mention_is_removed() -> None:
    assert read("<@1>さん") == ["さん"]


def test_custom_emoji_is_replaced_with_its_name() -> None:
    assert read("<:zunda:123> <a:mochi:456>") == ["zunda mochi"]


def test_all_stickers_are_read() -> None:
    assert read(stickers=("おはよう", "おやすみ")) == ["おはよう", "おやすみ"]


def test_attachment_only_message() -> None:
    assert read(attachments=("a.PNG",)) == ["画像ファイルが貼られたのだ"]


def test_attachment_with_text_is_appended_at_the_end() -> None:
    assert read("見て", attachments=("a.mp4",)) == ["見て", "かっこ、動画ファイルをみながら。"]


def test_all_attachment_kinds_are_read_once_each() -> None:
    result = read(attachments=("a.png", "b.jpg", "c.zip"))

    assert result == ["画像ファイルが貼られたのだ", "圧縮ファイルが貼られたのだ"]


@pytest.mark.parametrize("filename", ["a.unknown", "noextension"])
def test_unknown_attachment_kind(filename: str) -> None:
    assert read(attachments=(filename,)) == ["添付ファイルが貼られたのだ"]


def test_dictionary_prefers_longer_words() -> None:
    words = [("東京", "とうきょう"), ("東京都", "とうきょうと")]

    assert read("東京都、東京", words=words) == ["とうきょうと、とうきょう"]


def test_dictionary_does_not_replace_a_reading_again() -> None:
    assert read("AB", words=[("A", "B"), ("B", "C")]) == ["BC"]


def test_dictionary_treats_words_literally() -> None:
    assert read("a.c abc", words=[("a.c", "エー")]) == ["エー abc"]


def test_dictionary_applies_to_stickers_and_names() -> None:
    words = [("太郎", "たろう"), ("朝", "あさ")]

    assert read("<@1>", words=words, users={1: "太郎"}, stickers=("朝",)) == ["たろう", "あさ"]


def test_text_is_cut_at_the_limit() -> None:
    assert read("あいうえお", max_chars=3) == ["あいう以下略"]


def test_text_at_the_limit_is_not_cut() -> None:
    assert read("あいう", max_chars=3) == ["あいう"]


def test_limit_applies_to_the_whole_message() -> None:
    assert read("あいう\nえおか", max_chars=5) == ["あいう", "え以下略"]


def test_attachment_suffix_is_not_cut() -> None:
    assert read("あいうえお", max_chars=3, attachments=("a.txt",)) == [
        "あいう以下略",
        "かっこ、テキストファイルをみながら。",
    ]


def test_empty_message_is_not_read() -> None:
    assert read("") == []
    assert read("   \n ") == []


def test_incoming_from_discord_uses_resolved_objects() -> None:
    def named(id: int = 0, name: str = "", display_name: str = "") -> SimpleNamespace:
        return SimpleNamespace(id=id, name=name, display_name=display_name, filename=name)

    message = SimpleNamespace(
        content="本文",
        stickers=[named(name="スタンプ")],
        attachments=[named(name="a.png")],
        mentions=[named(id=1, display_name="表示名")],
        role_mentions=[named(id=2, name="ロール")],
        channel_mentions=[named(id=3, name="チャンネル")],
    )

    incoming = incoming_from_discord(message)

    assert incoming == IncomingMessage(
        content="本文",
        stickers=("スタンプ",),
        attachments=("a.png",),
        users={1: "表示名"},
        roles={2: "ロール"},
        channels={3: "チャンネル"},
    )
