#!/usr/bin/env python3
"""Update callers to use repository classes instead of functional imports."""

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


def _module_from_path(path: Path) -> str | None:
    parts = path.parts
    if "app" not in parts:
        return None
    return parts[parts.index("app") + 1]


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


def _receiver(module: str, *, same_module: bool) -> str:
    if same_module:
        return "self._repo"
    return f"{_repo_class_name(module)}(self._session)"


def _replace_function_calls(
    text: str,
    fn_name: str,
    module: str,
    method: str,
    *,
    targets: set[str],
) -> str:
    receiver_self = _receiver(module, same_module=True)
    receiver_cross = _receiver(module, same_module=False)
    class_receiver = f"{_repo_class_name(module)}(session)"

    patterns: list[tuple[str, str]] = []
    if "self" in targets:
        patterns.extend(
            [
                (
                    rf"\bawait\s+{re.escape(fn_name)}\(\s*self\._session\s*,",
                    f"await {receiver_cross}.{method}(",
                ),
                (
                    rf"\bawait\s+{re.escape(fn_name)}\(\s*self\._session\s*\)",
                    f"await {receiver_cross}.{method}()",
                ),
                (
                    rf"\bawait\s+repository\.{re.escape(fn_name)}\(\s*self\._session\s*,",
                    f"await {receiver_self}.{method}(",
                ),
                (
                    rf"\bawait\s+repository\.{re.escape(fn_name)}\(\s*self\._session\s*\)",
                    f"await {receiver_self}.{method}()",
                ),
                (
                    rf"\brepository\.{re.escape(fn_name)}\(\s*self\._session\s*,",
                    f"{receiver_self}.{method}(",
                ),
                (
                    rf"\brepository\.{re.escape(fn_name)}\(\s*self\._session\s*\)",
                    f"{receiver_self}.{method}()",
                ),
            ]
        )
    if "session" in targets:
        patterns.extend(
            [
                (
                    rf"\bawait\s+{re.escape(fn_name)}\(\s*session\s*,",
                    f"await {class_receiver}.{method}(",
                ),
                (
                    rf"\bawait\s+{re.escape(fn_name)}\(\s*session\s*\)",
                    f"await {class_receiver}.{method}()",
                ),
                (rf"\b{re.escape(fn_name)}\(\s*session\s*,", f"{class_receiver}.{method}("),
                (rf"\b{re.escape(fn_name)}\(\s*session\s*\)", f"{class_receiver}.{method}()"),
            ]
        )

    for pattern, repl in patterns:
        text = re.sub(pattern, repl, text)
    return text


def _replace_same_module_import(text: str, module: str, class_name: str) -> str:
    text = re.sub(
        rf"from app\.{re.escape(module)}\.repository import \([\s\S]*?\)\n",
        f"from app.{module}.repository import {class_name}\n",
        text,
        count=1,
    )
    text = re.sub(
        rf"from app\.{re.escape(module)}\.repository import [^\n]+\n",
        f"from app.{module}.repository import {class_name}\n",
        text,
        count=1,
    )
    text = text.replace(
        "from . import repository\n", f"from app.{module}.repository import {class_name}\n"
    )
    return text


def _ensure_repo_init(text: str, class_name: str, service_class: str) -> str:
    if "self._repo" in text:
        return text
    marker = f"class {service_class}"
    if marker not in text:
        return text
    return text.replace(
        "        self._session = session\n",
        f"        self._session = session\n        self._repo = {class_name}(session)\n",
        1,
    )


def _service_class_name(module: str) -> str:
    return "".join(part.capitalize() for part in module.split("_")) + "Service"


def update_service(path: Path, fn_map: dict[str, tuple[str, str]]) -> None:
    module = _module_from_path(path)
    if module is None:
        return

    class_name = _repo_class_name(module)
    text = path.read_text()
    text = _replace_same_module_import(text, module, class_name)
    text = _ensure_repo_init(text, class_name, _service_class_name(module))

    for fn_name, (mod, method) in fn_map.items():
        if fn_name in text or f"repository.{fn_name}" in text:
            if mod == module:
                text = _replace_function_calls(text, fn_name, mod, method, targets={"self"})
                text = re.sub(
                    rf"\bawait\s+{re.escape(fn_name)}\(\s*self\._session\s*,",
                    f"await self._repo.{method}(",
                    text,
                )
                text = re.sub(
                    rf"\bawait\s+{re.escape(fn_name)}\(\s*self\._session\s*\)",
                    f"await self._repo.{method}()",
                    text,
                )
            elif fn_name in text:
                text = _replace_function_calls(text, fn_name, mod, method, targets={"self"})

    used_cross = {
        _repo_class_name(mod)
        for fn, (mod, _) in fn_map.items()
        if mod != module and f"{_repo_class_name(mod)}(self._session)" in text
    }
    for cross_class in sorted(used_cross):
        mod = cross_class.removesuffix("Repository")
        snake = re.sub(r"(?<!^)(?=[A-Z])", "_", mod).lower()
        if f"from app.{snake}.repository import {cross_class}" not in text:
            lines = text.splitlines()
            insert_at = 0
            for idx, line in enumerate(lines):
                if line.startswith("from app."):
                    insert_at = idx + 1
            lines.insert(insert_at, f"from app.{snake}.repository import {cross_class}")
            text = "\n".join(lines) + ("\n" if text.endswith("\n") else "")

    # Drop stale functional imports from cross-module repository lines.
    text = re.sub(
        r"from app\.(\w+)\.repository import [a-z_,\s]+(?: as \w+)?\n(?=from app\.\1\.repository import \w+Repository)",
        "",
        text,
    )
    text = re.sub(
        r"from app\.(\w+)\.repository import [a-z_,\s]+(?: as \w+)?\n(?!from app\.\1\.repository import \w+Repository)",
        lambda m: "" if "Repository" not in m.group(0) else m.group(0),
        text,
    )

    path.write_text(text)


def update_generic(path: Path, fn_map: dict[str, tuple[str, str]]) -> None:
    text = path.read_text()
    original = text

    for fn_name, (mod, method) in fn_map.items():
        if fn_name not in text and f"{_repo_class_name(mod)}(session)" not in text:
            continue
        text = _replace_function_calls(text, fn_name, mod, method, targets={"session"})

    used_modules = sorted(
        {
            mod
            for fn, (mod, method) in fn_map.items()
            if f"{_repo_class_name(mod)}(session)" in text or fn in original
        }
    )
    for mod in used_modules:
        class_name = _repo_class_name(mod)
        text = re.sub(
            rf"from app\.{re.escape(mod)}\.repository import [\s\S]*?\)\n",
            f"from app.{mod}.repository import {class_name}\n",
            text,
            count=1,
        )
        text = re.sub(
            rf"from app\.{re.escape(mod)}\.repository import [^\n]+\n",
            f"from app.{mod}.repository import {class_name}\n",
            text,
            count=1,
        )

    if text != original:
        path.write_text(text)


def fix_variant_cross_repo() -> None:
    path = APP / "variant" / "repository.py"
    text = path.read_text()
    if "VariantConfigRepository" in text:
        return
    text = text.replace(
        "from app.variant_config.repository import create_variant_product_option_values, read_configs_by_variant_ids, soft_delete_configs_by_variant_id, soft_delete_configs_by_variant_ids\n",
        "from app.variant_config.repository import VariantConfigRepository\n",
    )
    for old, new in [
        (
            "create_variant_product_option_values(self._session,",
            "VariantConfigRepository(self._session).create_variant_product_option_values(",
        ),
        (
            "soft_delete_configs_by_variant_id(self._session,",
            "VariantConfigRepository(self._session).soft_delete_configs_by_variant_id(",
        ),
        (
            "soft_delete_configs_by_variant_ids(self._session,",
            "VariantConfigRepository(self._session).soft_delete_configs_by_variant_ids(",
        ),
        (
            "read_configs_by_variant_ids(self._session,",
            "VariantConfigRepository(self._session).read_configs_by_variant_ids(",
        ),
    ]:
        text = text.replace(old, new)
    path.write_text(text)


def remove_business_wrappers() -> None:
    path = APP / "business" / "repository.py"
    text = path.read_text()
    marker = "\n\nasync def create_business"
    if marker in text:
        path.write_text(text[: text.index(marker)] + "\n")


def main() -> None:
    fn_map = build_function_map()
    for path in sorted(APP.glob("*/service.py")):
        update_service(path, fn_map)
    for path in [
        *APP.glob("*/query.py"),
        REPO_ROOT / "scripts" / "seed_defaults.py",
        REPO_ROOT / "scripts" / "seed_smoke_test.py",
        REPO_ROOT / "scripts" / "seed_super_admin.py",
        REPO_ROOT / "scripts" / "upload_seeds.py",
        REPO_ROOT / "tests" / "test_genre_repository.py",
    ]:
        if path.exists():
            update_generic(path, fn_map)
    fix_variant_cross_repo()
    remove_business_wrappers()
    print("Repository caller migration complete")


if __name__ == "__main__":
    main()
