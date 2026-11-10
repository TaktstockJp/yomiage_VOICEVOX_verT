"""ログをコンソールと logs/ 以下のファイルに出力する設定。"""

from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

_FORMAT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
_MAX_BYTES = 1_000_000
_BACKUP_COUNT = 3


def setup_logging(log_dir: Path, level: int = logging.INFO) -> None:
    """ルートロガーを設定する。呼び直すと、前回の設定を置き換える。"""
    log_dir.mkdir(parents=True, exist_ok=True)
    formatter = logging.Formatter(_FORMAT)

    console = logging.StreamHandler()
    console.setFormatter(formatter)

    file = RotatingFileHandler(
        log_dir / "yomiage.log",
        maxBytes=_MAX_BYTES,
        backupCount=_BACKUP_COUNT,
        encoding="utf-8",
    )
    file.setFormatter(formatter)

    root = logging.getLogger()
    for handler in root.handlers[:]:
        root.removeHandler(handler)
        handler.close()
    root.addHandler(console)
    root.addHandler(file)
    root.setLevel(level)
