#!/usr/bin/env python3
"""Convert functional repository modules to class-based repositories."""

from __future__ import annotations

import ast
import re
import textwrap
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
APP = REPO_ROOT / "app"

SKIP_MODULES = frozenset()


class SessionToSelf(ast.NodeTransformer):
    def __init__(self, method_names: set[str]) -> None:
        self._method_names = method_names

    def visit_Name(self, node: ast.Name) -> ast.AST:
        if node.id == "session":
            return ast.Attribute(
                value=ast.Name(id="self", ctx=ast.Load()), attr="_session", ctx=node.ctx
            )
        return node

    def visit_Call(self, node: ast.Call) -> ast.AST:
        self.generic_visit(node)
        if isinstance(node.func, ast.Name) and node.func.id in self._method_names:
            if node.args and isinstance(node.args[0], (ast.Name, ast.Attribute)):
                first = node.args[0]
                if (isinstance(first, ast.Name) and first.id == "session") or (
                    isinstance(first, ast.Attribute)
                    and isinstance(first.value, ast.Name)
                    and first.value.id == "self"
                    and first.attr == "_session"
                ):
                    node.func = ast.Attribute(
                        value=ast.Name(id="self", ctx=ast.Load()),
                        attr=node.func.id,
                        ctx=ast.Load(),
                    )
                    node.args = node.args[1:]
        return node


def _repo_class_name(module: str) -> str:
    return "".join(part.capitalize() for part in module.split("_")) + "Repository"


def _convert_function(
    source: str,
    node: ast.AsyncFunctionDef,
    method_names: set[str],
) -> str:
    fn_source = ast.get_source_segment(source, node)
    if fn_source is None:
        raise ValueError(f"Could not extract source for {node.name}")

    fn_tree = ast.parse(fn_source)
    fn = fn_tree.body[0]
    assert isinstance(fn, ast.AsyncFunctionDef)

    if not fn.args.args or fn.args.args[0].arg != "session":
        raise ValueError(f"{node.name} does not take session as first argument")

    fn.args.args = [ast.arg(arg="self"), *fn.args.args[1:]]
    fn = SessionToSelf(method_names).visit(fn)
    assert isinstance(fn, ast.AsyncFunctionDef)

    fn.name = node.name
    unparsed = ast.unparse(fn)
    return textwrap.indent(unparsed, "    ")


def convert_repository(module: str) -> bool:
    path = APP / module / "repository.py"
    if not path.exists():
        return False

    source = path.read_text()
    class_name = _repo_class_name(module)
    if f"class {class_name}" in source:
        return False

    tree = ast.parse(source)
    header_nodes: list[ast.stmt] = []
    async_fns: list[ast.AsyncFunctionDef] = []

    for node in tree.body:
        if isinstance(node, ast.AsyncFunctionDef):
            if node.args.args and node.args.args[0].arg == "session":
                async_fns.append(node)
            else:
                header_nodes.append(node)
        elif isinstance(node, ast.ClassDef):
            return False
        else:
            header_nodes.append(node)

    if not async_fns:
        return False

    method_names = {fn.name for fn in async_fns}
    header = "\n".join(ast.unparse(n) for n in header_nodes).strip()
    if header:
        header += "\n\n"

    methods = "\n\n".join(_convert_function(source, fn, method_names) for fn in async_fns)

    output = (
        f"{header}"
        f"class {class_name}:\n"
        f"    def __init__(self, session: AsyncSession) -> None:\n"
        f"        self._session = session\n\n"
        f"{methods}\n"
    )

    if "from __future__ import annotations" not in output:
        output = "from __future__ import annotations\n\n" + output

    path.write_text(output)
    return True


def main() -> None:
    converted: list[str] = []
    for path in sorted(APP.glob("*/repository.py")):
        module = path.parent.name
        if module in SKIP_MODULES:
            continue
        if convert_repository(module):
            converted.append(module)
    print(f"Converted {len(converted)} repositories:")
    for name in converted:
        print(f"  - {name}")


if __name__ == "__main__":
    main()
