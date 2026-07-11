"""CI guards for privilege catalog and route authorization."""

from __future__ import annotations

import ast
import re
from pathlib import Path

from app.auth.privilege_catalog import (
    DEPRECATED_PRIVILEGE_CODES,
    all_catalog_privilege_codes,
    business_privilege_defs,
    owner_default_privilege_codes,
)

REPO_ROOT = Path(__file__).resolve().parent.parent
APP_DIR = REPO_ROOT / "app"

PRIVILEGE_RE = re.compile(r'require_privilege(?:_and_owner)?\(\s*["\']([^"\']+)["\']')

# Routes that intentionally use require_context("BUSINESS") without a privilege guard.
KNOWN_UNGUARDED_BUSINESS_ROUTES: frozenset[str] = frozenset(
    {
        "GET /businesses",
        "GET /businesses/{id}",
    }
)


def _controller_files() -> list[Path]:
    return sorted(APP_DIR.glob("**/controller.py"))


def _collect_privilege_usages() -> set[str]:
    codes: set[str] = set()
    for path in _controller_files():
        text = path.read_text(encoding="utf-8")
        codes.update(PRIVILEGE_RE.findall(text))
    return codes


def _route_key(method: str, path: str) -> str:
    return f"{method.upper()} {path}"


def _collect_business_context_only_routes() -> set[str]:
    unguarded: set[str] = set()
    for path in _controller_files():
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        prefix = ""
        for node in tree.body:
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id == "router":
                        if isinstance(node.value, ast.Call):
                            for kw in node.value.keywords:
                                if kw.arg == "prefix" and isinstance(kw.value, ast.Constant):
                                    prefix = str(kw.value.value)

        for node in tree.body:
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            for dec in node.decorator_list:
                if not isinstance(dec, ast.Call):
                    continue
                func = dec.func
                if not (
                    isinstance(func, ast.Attribute)
                    and func.attr in {"get", "post", "put", "patch", "delete"}
                ):
                    continue
                route_path = prefix
                if dec.args and isinstance(dec.args[0], ast.Constant):
                    route_path += str(dec.args[0].value)
                source = ast.get_source_segment(path.read_text(encoding="utf-8"), node) or ""
                has_context = 'require_context("BUSINESS")' in source
                has_privilege = (
                    "require_privilege" in source
                    or "require_owner" in source
                )
                if has_context and not has_privilege:
                    unguarded.add(_route_key(func.attr, route_path))
    return unguarded


class TestPrivilegeCatalog:
    def test_business_privilege_codes_are_unique(self) -> None:
        codes = [p.code for p in business_privilege_defs()]
        assert len(codes) == len(set(codes))

    def test_owner_defaults_are_catalogued(self) -> None:
        owner_codes = owner_default_privilege_codes()
        assert "READ_VARIANT" in owner_codes
        assert "CREATE_VARIANT" in owner_codes
        assert "UPDATE_ORDER" in owner_codes


class TestRouteAuthorization:
    def test_controller_privileges_exist_in_catalog(self) -> None:
        used = _collect_privilege_usages()
        catalog = all_catalog_privilege_codes()
        unknown = sorted(used - catalog)
        assert unknown == [], f"Unknown privilege codes in controllers: {unknown}"

    def test_deprecated_privileges_not_used(self) -> None:
        used = _collect_privilege_usages()
        deprecated_used = sorted(used & DEPRECATED_PRIVILEGE_CODES)
        assert deprecated_used == [], (
            f"Deprecated privilege codes still referenced: {deprecated_used}"
        )

    def test_business_context_only_routes_are_allowlisted(self) -> None:
        unguarded = _collect_business_context_only_routes()
        new_violations = sorted(unguarded - KNOWN_UNGUARDED_BUSINESS_ROUTES)
        assert new_violations == [], (
            "BUSINESS routes with only require_context (no privilege/owner): "
            f"{new_violations}. Add require_privilege or extend KNOWN_UNGUARDED_BUSINESS_ROUTES."
        )

    def test_allowlist_has_no_stale_entries(self) -> None:
        unguarded = _collect_business_context_only_routes()
        stale = sorted(KNOWN_UNGUARDED_BUSINESS_ROUTES - unguarded)
        assert stale == [], f"Remove fixed routes from KNOWN_UNGUARDED_BUSINESS_ROUTES: {stale}"
