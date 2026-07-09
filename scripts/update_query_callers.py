#!/usr/bin/env python3
"""Update query.py, scripts, and tests to use repository classes."""

from __future__ import annotations

import ast
import re
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
APP = REPO_ROOT / "app"

BUSINESS_METHOD_MAP = {
    "create_business": "create",
    "update_business": "update",
    "delete_business": "delete",
    "read_business_by_id": "read_by_id",
    "read_business_by_user_id": "read_by_user_id",
    "count_businesses": "count",
    "list_businesses": "list",
}


def _repo_class_name(module: str) -> str:
    return "".join(part.capitalize() for part in module.split("_")) + "Repository"


def build_function_map() -> dict[str, tuple[str, str]]:
    mapping: dict[str, tuple[str, str]] = {}
    for path in sorted(APP.glob("*/repository.py")):
        module = path.parent.name
        class_name = _repo_class_name(module)
        source = path.read_text()
        if f"class {class_name}" not in source:
            continue
        tree = ast.parse(source)
        for node in tree.body:
            if not isinstance(node, ast.ClassDef) or node.name != class_name:
                continue
            for item in node.body:
                if isinstance(item, ast.AsyncFunctionDef) and item.name != "__init__":
                    mapping[item.name] = (module, item.name)
    for fn, method in BUSINESS_METHOD_MAP.items():
        mapping[fn] = ("business", method)
    return mapping


def _replace_calls(text: str, fn_map: dict[str, tuple[str, str]]) -> str:
    for fn_name, (mod, method) in sorted(fn_map.items(), key=lambda x: len(x[0]), reverse=True):
        if fn_name not in text:
            continue
        cls = _repo_class_name(mod)
        text = re.sub(
            rf"\bawait\s+{re.escape(fn_name)}\(\s*session\s*,",
            f"await {cls}(session).{method}(",
            text,
        )
        text = re.sub(
            rf"\bawait\s+{re.escape(fn_name)}\(\s*session\s*\)",
            f"await {cls}(session).{method}()",
            text,
        )
        text = re.sub(
            rf"\b{re.escape(fn_name)}\(\s*session\s*,",
            f"{cls}(session).{method}(",
            text,
        )
        text = re.sub(
            rf"\b{re.escape(fn_name)}\(\s*session\s*\)",
            f"{cls}(session).{method}()",
            text,
        )
    return text


def _update_imports(text: str, fn_map: dict[str, tuple[str, str]]) -> str:
    used_modules: set[str] = set()
    for fn_name, (mod, _) in fn_map.items():
        cls = _repo_class_name(mod)
        if f"{cls}(session)" in text:
            used_modules.add(mod)

    lines = text.splitlines()
    new_lines: list[str] = []
    i = 0
    while i < len(lines):
        line = lines[i]
        m = re.match(r"from app\.(\w+)\.repository import ", line)
        if m:
            mod = m.group(1)
            if mod in used_modules:
                # consume whole import statement
                if "(" in line and ")" not in line:
                    block = [line]
                    i += 1
                    while i < len(lines):
                        block.append(lines[i])
                        if ")" in lines[i]:
                            i += 1
                            break
                        i += 1
                    new_lines.append(f"from app.{mod}.repository import {_repo_class_name(mod)}")
                    continue
                new_lines.append(f"from app.{mod}.repository import {_repo_class_name(mod)}")
                i += 1
                continue
        new_lines.append(line)
        i += 1
    return "\n".join(new_lines) + ("\n" if text.endswith("\n") else "")


def update_file(path: Path, fn_map: dict[str, tuple[str, str]]) -> bool:
    original = path.read_text()
    text = _replace_calls(original, fn_map)
    text = _update_imports(text, fn_map)
    if text != original:
        path.write_text(text)
        return True
    return False


def main() -> None:
    fn_map = build_function_map()
    paths = [
        *APP.glob("*/query.py"),
        REPO_ROOT / "scripts" / "seed_defaults.py",
        REPO_ROOT / "scripts" / "seed_smoke_test.py",
        REPO_ROOT / "scripts" / "seed_super_admin.py",
        REPO_ROOT / "scripts" / "upload_seeds.py",
        REPO_ROOT / "tests" / "test_genre_repository.py",
    ]
    changed = sum(1 for p in paths if p.exists() and update_file(p, fn_map))
    print(f"Updated {changed} files")


if __name__ == "__main__":
    main()
