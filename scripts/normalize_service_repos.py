#!/usr/bin/env python3
"""Normalize same-module service calls to use self._repo."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).parent.parent / "app"


def _class_name(module: str) -> str:
    return "".join(p.capitalize() for p in module.split("_")) + "Repository"


def fix_service(path: Path) -> bool:
    module = path.parent.name
    cls = _class_name(module)
    text = path.read_text()
    updated = text.replace(f"{cls}(self._session).", "self._repo.")
    updated = re.sub(
        rf"from app\.{re.escape(module)}\.repository import [\s\S]*?\)\n",
        f"from app.{module}.repository import {cls}\n",
        updated,
        count=1,
    )
    updated = re.sub(
        rf"(from app\.{re.escape(module)}\.repository import {cls}\n)+",
        f"from app.{module}.repository import {cls}\n",
        updated,
    )
    if updated != text:
        path.write_text(updated)
        return True
    return False


def main() -> None:
    changed = sum(fix_service(p) for p in sorted(ROOT.glob("*/service.py")))
    print(f"Normalized {changed} service files")


if __name__ == "__main__":
    main()
