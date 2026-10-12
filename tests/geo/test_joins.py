"""Corner blending and join census."""

from __future__ import annotations

from typekernel.geo.joins import (
    angle_range,
    blend_corners,
    classify_joins,
    curvature_jump,
)
from typekernel.geo.path_builder import PathBuilder


def _triangle():  # type: ignore[no-untyped-def]
    b = PathBuilder()
    b.moveTo(0, 0)
    b.lineTo(400, 0)
    b.lineTo(200, 300)
    b.closePath()
    return b.build()


def test_blend_corners_removes_all_selected_corners() -> None:
    tri = _triangle()
    before = classify_joins(tri)
    assert before.corners == 3
    after = classify_joins(blend_corners(tri, 40.0))
    assert after.corners == 0
    assert after.kinks == 0


def test_blend_is_g2_against_lines() -> None:
    smooth = blend_corners(_triangle(), 40.0)
    assert curvature_jump(smooth) < 1e-6


def test_selector_limits_blending() -> None:
    tri = _triangle()
    none = blend_corners(tri, 40.0, select=angle_range(170.0, 180.0))
    assert classify_joins(none).corners == 3
