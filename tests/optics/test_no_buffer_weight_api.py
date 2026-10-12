"""Guard: optics must not grow a public buffer / stroke-weight API."""

from __future__ import annotations

import ast
from pathlib import Path

from typekernel import optics

FORBIDDEN_NAMES = frozenset(
    {
        "buffer",
        "buffer_weight",
        "stroke_width_for_weight",
        "expand_stroke_weight",
    }
)

OPTICS_SRC = Path(__file__).parents[2] / "src" / "typekernel" / "optics"


def test_optics_public_names_forbid_buffer_weight() -> None:
    public = set(getattr(optics, "__all__", [])) | {
        name for name in dir(optics) if not name.startswith("_")
    }
    offenders = public & FORBIDDEN_NAMES
    assert not offenders, f"forbidden public optics names: {sorted(offenders)}"


def test_optics_modules_have_no_forbidden_defs() -> None:
    for path in OPTICS_SRC.glob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                assert node.name not in FORBIDDEN_NAMES, (
                    f"{path.name} defines forbidden symbol {node.name!r}"
                )
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        assert target.id not in FORBIDDEN_NAMES, (
                            f"{path.name} assigns forbidden name {target.id!r}"
                        )


def test_optics_has_no_shapely_imports() -> None:
    for path in OPTICS_SRC.glob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    assert not alias.name.startswith("shapely"), path.name
            if isinstance(node, ast.ImportFrom) and node.module is not None:
                assert not node.module.startswith("shapely"), path.name
