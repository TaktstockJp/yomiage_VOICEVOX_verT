import logging
from pathlib import Path

import pytest

from yomiage.logs import setup_logging


@pytest.fixture
def restore_root_logger():
    root = logging.getLogger()
    handlers = root.handlers[:]
    level = root.level
    root.handlers[:] = []
    yield
    for handler in root.handlers[:]:
        root.removeHandler(handler)
        handler.close()
    root.handlers[:] = handlers
    root.setLevel(level)


@pytest.mark.usefixtures("restore_root_logger")
def test_logs_are_written_as_utf8_and_setup_is_repeatable(tmp_path: Path) -> None:
    log_dir = tmp_path / "logs"

    setup_logging(log_dir)
    setup_logging(log_dir)
    logging.getLogger("test").info("読み上げのログ")

    assert len(logging.getLogger().handlers) == 2
    lines = (log_dir / "yomiage.log").read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1
    assert "読み上げのログ" in lines[0]
