"""Guard: axes must not expose buffer / stroke-weight helpers."""

from __future__ import annotations

import ast
from pathlib import Path

from typekernel import axes

FORBIDDEN_NAMES = frozenset(
    {
        "buffer",
        "buffer_weight",
        "stroke_width_for_weight",
        "expand_stroke_weight",
        "STROKES",
        "italic_shear",
    }
)

AXES_SRC = Path(__file__).parents[2] / "src" / "typekernel" / "axes"


def test_axes_public_names_forbid_buffer_weight() -> None:
    public = set(getattr(axes, "__all__", [])) | {
        name for name in dir(axes) if not name.startswith("_")
    }
    offenders = public & FORBIDDEN_NAMES
    assert not offenders, f"forbidden public axes names: {sorted(offenders)}"


def test_axes_modules_have_no_forbidden_defs() -> None:
    for path in AXES_SRC.glob("*.py"):
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


def test_axes_has_no_shapely_imports() -> None:
    for path in AXES_SRC.glob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    assert not alias.name.startswith("shapely"), path.name
            if isinstance(node, ast.ImportFrom) and node.module is not None:
                assert not node.module.startswith("shapely"), path.name


def test_oblique_transform_exists_and_no_italic_shear() -> None:
    assert "ObliqueTransform" in axes.__all__
    assert "italic_shear" not in axes.__all__
    assert not hasattr(axes, "italic_shear")
