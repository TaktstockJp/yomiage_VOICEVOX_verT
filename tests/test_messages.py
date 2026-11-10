from yomiage import messages


def test_time_signal_exists_for_every_hour() -> None:
    assert sorted(messages.TIME_SIGNALS) == list(range(24))


def test_attachment_extensions_are_normalized() -> None:
    assert all(ext.startswith(".") and ext == ext.lower() for ext in messages.ATTACHMENT_KINDS)
