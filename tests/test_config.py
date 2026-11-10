from pathlib import Path

import pytest

from yomiage.config import ConfigError, load_config

ROOT = Path(__file__).resolve().parent.parent


def write(tmp_path: Path, text: str) -> Path:
    path = tmp_path / "config.toml"
    path.write_text(text, encoding="utf-8")
    return path


def test_example_file_loads_once_token_is_filled(tmp_path: Path) -> None:
    example = (ROOT / "config.example.toml").read_text(encoding="utf-8")
    config = load_config(write(tmp_path, example.replace('token = ""', 'token = "abc"', 1)))

    assert config.discord.token == "abc"
    assert config.discord.ignore_prefixes == ("$", "?")
    assert config.default_voice.speaker == "ずんだもん"
    assert [(e.name, e.port) for e in config.engines.voicevox] == [("VOICEVOX", 50021)]
    assert config.engines.coeiroink.enabled is False
    assert config.engines.voisona.port == 32766


def test_optional_sections_use_defaults(tmp_path: Path) -> None:
    config = load_config(write(tmp_path, '[discord]\ntoken = "abc"\n'))

    assert config.discord.command_prefix == "!"
    assert config.ffmpeg.path == ""
    assert config.engines.voicevox == ()


def test_multiple_voicevox_compatible_engines(tmp_path: Path) -> None:
    config = load_config(
        write(
            tmp_path,
            '[discord]\ntoken = "abc"\n'
            '[[engines.voicevox]]\nname = "VOICEVOX"\nport = 50021\n'
            '[[engines.voicevox]]\nname = "AivisSpeech"\nport = 10101\n',
        )
    )

    assert [e.name for e in config.engines.voicevox] == ["VOICEVOX", "AivisSpeech"]


def test_secrets_are_not_in_repr(tmp_path: Path) -> None:
    config = load_config(
        write(
            tmp_path,
            '[discord]\ntoken = "secret-token"\n'
            '[engines.voisona]\nenabled = true\nuser = "secret-user"\npassword = "secret-password"\n',
        )
    )

    assert "secret" not in repr(config)


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ('[discord]\ntoken = ""\n', "token"),
        ("[discord]\n", "token"),
        ("[discord]\ntoken = 1\n", "token"),
        ('[discord]\ntoken = "a"\nignore_prefixes = [""]\n', "ignore_prefixes"),
        ('[discord]\ntoken = "a"\n[[engines.voicevox]]\nname = "A"\nport = 0\n', "port"),
        ('[discord]\ntoken = "a"\n[[engines.voicevox]]\nname = "A"\nport = true\n', "port"),
        (
            '[discord]\ntoken = "a"\n'
            '[[engines.voicevox]]\nname = "A"\nport = 1\n[[engines.voicevox]]\nname = "A"\nport = 2\n',
            "同じ name",
        ),
        ('[discord]\ntoken = "a"\n[engines.voisona]\nenabled = true\n', "user"),
        ("not toml", "書き方"),
    ],
)
def test_invalid_config_is_reported(tmp_path: Path, text: str, expected: str) -> None:
    with pytest.raises(ConfigError, match=expected):
        load_config(write(tmp_path, text))


def test_missing_file_is_reported(tmp_path: Path) -> None:
    with pytest.raises(ConfigError, match="見つかりません"):
        load_config(tmp_path / "config.toml")
