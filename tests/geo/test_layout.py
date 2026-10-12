"""Tests for metrics / word layout helpers."""

from __future__ import annotations

from typekernel.geo.layout import (
    GlyphMetrics,
    ink_origin_x,
    layout_x_positions,
    metrics_from_sidebearings,
    union_bounds,
)
from typekernel.geo.path_builder import PathBuilder


def _box(x0: float, y0: float, x1: float, y1: float):
    b = PathBuilder()
    b.moveTo(x0, y0)
    b.lineTo(x1, y0)
    b.lineTo(x1, y1)
    b.lineTo(x0, y1)
    b.closePath()
    return b.build()


def test_metrics_and_ink_origin() -> None:
    outline = _box(10, 0, 110, 100)
    m = metrics_from_sidebearings(outline, 20, 30)
    assert m.advance == 20 + 100 + 30
    assert ink_origin_x(m) == 10.0  # 20 - 10


def test_layout_x_positions_with_tracking() -> None:
    xs = layout_x_positions([100.0, 80.0, 90.0], tracking=10.0)
    assert xs == [0.0, 110.0, 200.0]


def test_union_bounds() -> None:
    a = _box(0, 0, 10, 10)
    b = _box(5, -5, 20, 8)
    assert union_bounds([a, b]) == (0, -5, 20, 10)


def test_glyph_metrics_frozen() -> None:
    m = GlyphMetrics(1, 2, 3, 0, 0)
    assert m.left_sidebearing == 1
