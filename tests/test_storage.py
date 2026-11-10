from pathlib import Path

import pytest

from yomiage.storage import Settings, Storage
from yomiage.tts.base import VoiceSelection

VOICE = VoiceSelection("VOICEVOX", "ずんだもん", "ノーマル")
OTHER_VOICE = VoiceSelection("VOICEVOX", "ずんだもん", "あまあま")


@pytest.fixture
def storage():
    instance = Storage(":memory:")
    yield instance
    instance.close()


def test_user_voice_round_trip(storage: Storage) -> None:
    assert storage.user_voice(1) is None

    storage.set_user_voice(1, VOICE)
    storage.set_user_voice(1, OTHER_VOICE)

    assert storage.user_voice(1) == OTHER_VOICE


def test_style_params_are_scoped_to_the_style(storage: Storage) -> None:
    storage.set_style_param(VOICE, "speed", 1.5)
    storage.set_style_param(VOICE, "pitch", 0.1)
    storage.set_style_param(OTHER_VOICE, "speed", 0.8)

    assert storage.style_params(VOICE) == {"speed": 1.5, "pitch": 0.1}

    storage.delete_style_param(VOICE, "speed")

    assert storage.style_params(VOICE) == {"pitch": 0.1}
    assert storage.style_params(OTHER_VOICE) == {"speed": 0.8}


def test_words_are_ordered_longest_first(storage: Storage) -> None:
    storage.set_word("短", "みじかい")
    storage.set_word("とても長い単語", "ながい")
    storage.set_word("中くらい", "ちゅう")

    assert [word for word, _ in storage.words()] == ["とても長い単語", "中くらい", "短"]


def test_set_word_overwrites_the_reading(storage: Storage) -> None:
    storage.set_word("A", "えー")
    storage.set_word("A", "エース")

    assert storage.words() == [("A", "エース")]


def test_delete_word_reports_whether_it_existed(storage: Storage) -> None:
    storage.set_word("A", "えー")

    assert storage.delete_word("A") is True
    assert storage.delete_word("A") is False


def test_settings_default_and_types(storage: Storage) -> None:
    assert storage.settings() == Settings()

    storage.set_setting("auto_leave", False)
    storage.set_setting("max_chars", 120)
    settings = storage.settings()

    assert settings.auto_leave is False
    assert settings.max_chars == 120
    assert settings.time_signal is True


def test_unknown_setting_is_rejected(storage: Storage) -> None:
    with pytest.raises(KeyError):
        storage.set_setting("read_name", True)


def test_data_survives_reopening(tmp_path: Path) -> None:
    path = tmp_path / "yomiage.db"
    first = Storage(path)
    first.set_word("A", "えー")
    first.close()

    second = Storage(path)
    try:
        assert second.words() == [("A", "えー")]
    finally:
        second.close()
