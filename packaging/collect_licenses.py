"""実行時に同梱される Python パッケージのライセンスファイルを、指定のフォルダに集める。"""

from __future__ import annotations

import importlib.metadata as metadata
import re
import shutil
import sys
from pathlib import Path

from packaging.requirements import Requirement
from packaging.utils import canonicalize_name

_LICENSE_FILE = re.compile(r"(^|/)(licen[cs]e|copying|notice)[^/]*$", re.IGNORECASE)
# wheel にライセンスファイルが入っていないパッケージ。全文は THIRD_PARTY_NOTICES.md に記載している
_DOCUMENTED_ELSEWHERE = {"davey"}


def runtime_distributions(root: str) -> dict[str, metadata.Distribution]:
    found: dict[str, metadata.Distribution] = {}

    def visit(name: str, extras: frozenset[str]) -> None:
        key = canonicalize_name(name)
        if key in found:
            return
        distribution = metadata.distribution(name)
        found[key] = distribution
        for line in distribution.requires or []:
            requirement = Requirement(line)
            contexts = [{"extra": extra} for extra in extras] or [{"extra": ""}]
            if requirement.marker is None or any(requirement.marker.evaluate(c) for c in contexts):
                visit(requirement.name, frozenset(requirement.extras))

    visit(root, frozenset())
    del found[canonicalize_name(root)]
    return found


def main(output: Path) -> int:
    missing: list[str] = []
    for key, distribution in sorted(runtime_distributions("yomiage").items()):
        files = [file for file in distribution.files or [] if _LICENSE_FILE.search(str(file))]
        if not files:
            if key not in _DOCUMENTED_ELSEWHERE:
                missing.append(key)
            continue
        target = output / f"{key}-{distribution.version}"
        target.mkdir(parents=True, exist_ok=True)
        for file in files:
            shutil.copyfile(file.locate(), target / Path(str(file)).name)

    python_license = Path(sys.base_prefix) / "LICENSE.txt"
    python_target = output / f"python-{sys.version.split()[0]}"
    python_target.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(python_license, python_target / "LICENSE.txt")

    if missing:
        print("ライセンスファイルが見つかりません:", ", ".join(missing), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(Path(sys.argv[1])))
