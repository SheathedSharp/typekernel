"""Unit tests for optional boolean operations (skia-pathops)."""

from __future__ import annotations

import ast
import sys
from pathlib import Path

import pytest

import typekernel.geo
from typekernel.geo.boolean import BOOLEAN_OPS, boolean_op, strip_tiny_contours, union_all
from typekernel.geo.outline import Outline, bounds
from typekernel.geo.path_builder import PathBuilder


def _rect(x0: float, y0: float, x1: float, y1: float) -> Outline:
    b = PathBuilder()
    b.moveTo(x0, y0)
    b.lineTo(x1, y0)
    b.lineTo(x1, y1)
    b.lineTo(x0, y1)
    b.closePath()
    return b.build()


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
        boolean_op(_rect(0, 0, 10, 10), _rect(5, 5, 15, 15), "union")


@pytest.mark.skipif(
    __import__("importlib").util.find_spec("pathops") is None,
    reason="skia-pathops not installed",
)
def test_union_merges_overlapping_rects() -> None:
    a = _rect(0, 0, 100, 100)
    b = _rect(50, 50, 150, 150)
    merged = boolean_op(a, b, "union")
    assert merged.contour_count >= 1
    min_x, min_y, max_x, max_y = bounds(merged)
    assert min_x == pytest.approx(0.0, abs=1e-3)
    assert min_y == pytest.approx(0.0, abs=1e-3)
    assert max_x == pytest.approx(150.0, abs=1e-3)
    assert max_y == pytest.approx(150.0, abs=1e-3)


@pytest.mark.skipif(
    __import__("importlib").util.find_spec("pathops") is None,
    reason="skia-pathops not installed",
)
def test_union_all_of_three() -> None:
    parts = [_rect(0, 0, 40, 40), _rect(30, 0, 70, 40), _rect(60, 0, 100, 40)]
    merged = union_all(parts)
    min_x, _, max_x, _ = bounds(merged)
    assert min_x == pytest.approx(0.0, abs=1e-3)
    assert max_x == pytest.approx(100.0, abs=1e-3)


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


def test_strip_tiny_contours_drops_speck_keeps_body() -> None:
    body = _rect(0, 0, 100, 100)
    speck = _rect(2, 2, 3, 3)
    merged = Outline((*body.contours, *speck.contours))
    stripped = strip_tiny_contours(merged, min_area=10.0)
    assert len(stripped.contours) == 1
    assert bounds(stripped)[2] == pytest.approx(100.0, abs=1e-3)


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


def test_self_union_and_strip_tiny() -> None:
    pytest.importorskip("pathops")
    from typekernel.geo.boolean import self_union, strip_tiny_contours
    from typekernel.geo.contour import Contour, signed_area
    from typekernel.geo.outline import Outline
    from typekernel.geo.point import Point
    from typekernel.geo.segment import LineSegment

    big = _rect(0, 0, 100, 100)
    healed = self_union(big)
    assert healed.contour_count >= 1
    # Tiny square debris
    tiny = Outline(
        (
            Contour(
                (
                    LineSegment(Point(0, 0), Point(1, 0)),
                    LineSegment(Point(1, 0), Point(1, 1)),
                    LineSegment(Point(1, 1), Point(0, 1)),
                    LineSegment(Point(0, 1), Point(0, 0)),
                ),
                closed=True,
            ),
        )
    )
    merged = Outline(big.contours + tiny.contours)
    stripped = strip_tiny_contours(merged, min_area=50.0)
    assert all(abs(signed_area(c)) >= 50.0 for c in stripped.contours)
