"""Unit tests for the optional boolean stub."""

import ast
import sys
import types
from pathlib import Path

import pytest

import typekernel.geo
from typekernel.geo.boolean import BOOLEAN_OPS, boolean_op
from typekernel.geo.outline import Outline


def test_signature_accepts_two_outlines_and_an_operation() -> None:
    assert callable(boolean_op)
    assert BOOLEAN_OPS == {"union", "intersection", "difference"}


def test_unknown_operation_is_rejected_before_any_import() -> None:
    with pytest.raises(ValueError, match="unknown boolean op"):
        boolean_op(Outline(()), Outline(()), "xor")  # type: ignore[arg-type]


def test_missing_pathops_raises_runtime_error_with_install_hint(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setitem(sys.modules, "pathops", None)
    with pytest.raises(RuntimeError, match=r"typekernel\[boolean\]"):
        boolean_op(Outline(()), Outline(()), "union")


def test_with_pathops_available_the_round_trip_is_explicitly_unimplemented(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setitem(sys.modules, "pathops", types.ModuleType("pathops"))
    with pytest.raises(NotImplementedError, match="round-trip"):
        boolean_op(Outline(()), Outline(()), "difference")


def test_shapely_is_never_referenced() -> None:
    """Shapely would force polygonisation, so it must not appear at all."""
    source = Path(typekernel.geo.boolean.__file__).read_text(encoding="utf-8")
    tree = ast.parse(source)
    names = {node.id for node in ast.walk(tree) if isinstance(node, ast.Name)}
    modules = {
        alias.name.split(".")[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    } | {
        (node.module or "").split(".")[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom)
    }
    assert "shapely" not in names
    assert "shapely" not in modules


def test_boolean_extra_is_declared_but_not_required() -> None:
    """pathops must stay optional; the core install must not need it."""
    import tomllib

    root = Path(__file__).resolve().parents[2]
    config = tomllib.loads((root / "pyproject.toml").read_text(encoding="utf-8"))
    extras = config["project"]["optional-dependencies"]
    assert any("skia-pathops" in dep for dep in extras["boolean"])
    assert not any(
        "skia-pathops" in dep for dep in config["project"]["dependencies"]
    )
