"""construct builders — synthetic geometry only (测试清单)."""

from __future__ import annotations

import math

from typekernel.draw import (
    Fragment,
    diagonal_band,
    hook,
    spring,
    superellipse_quarter,
    tensioned_arc,
)
from typekernel.geo.point import Point
from typekernel.geo.segment import LineSegment
from typekernel.geo.smoothness import g1_join_error


def _unit(p: Point) -> Point:
    L = math.hypot(p.x, p.y)
    return Point(p.x / L, p.y / L)


def test_tensioned_arc_endpoints_and_tangents() -> None:
    frag = tensioned_arc((0, 0), (1, 0), (10, 0), (1, 0), tension=0.55)
    assert frag.start == Point(0.0, 0.0)
    assert frag.end == Point(10.0, 0.0)
    assert abs(frag.start_tangent().x - 1.0) < 1e-9
    assert abs(frag.end_tangent().x - 1.0) < 1e-9
    # G1 with adjacent collinear lines
    left = LineSegment(Point(-5, 0), Point(0, 0))
    right = LineSegment(Point(10, 0), Point(15, 0))
    assert g1_join_error(left, frag.segments[0]) < 1e-6
    assert g1_join_error(frag.segments[0], right) < 1e-6


def test_superellipse_quarter_endpoints() -> None:
    frag = superellipse_quarter((0, 0), 10, 8, 0, exponent=2.0)
    assert frag.start == Point(10.0, 0.0)
    assert frag.end == Point(0.0, 8.0)
    # Tangent at +x end should be vertical-ish (up), at +y end horizontal-ish (left)
    st = frag.start_tangent()
    et = frag.end_tangent()
    assert abs(st.x) < 1e-6 and st.y > 0
    assert et.x < 0 and abs(et.y) < 1e-6


def test_spring_g1_with_stem_line() -> None:
    frag = spring(0.0, 0.0, 20.0, toward=(30, 20), depth=8.0, tension=0.55)
    stem = LineSegment(Point(0, -10), Point(0, 0))
    assert g1_join_error(stem, frag.segments[0]) < 1e-6
    assert frag.start == Point(0.0, 0.0)
    assert math.isclose(frag.end.y, 20.0, abs_tol=1e-9)


def test_diagonal_band_perpendicular_width() -> None:
    left, right = diagonal_band((0, 100), (50, 0), weight=20.0, compensate=True)
    # Midpoints of each edge; distance along normal should be ~weight
    def mid(frag: Fragment) -> Point:
        a, b = frag.start, frag.end
        return Point((a.x + b.x) / 2, (a.y + b.y) / 2)

    m0, m1 = mid(left), mid(right)
    dist = math.hypot(m0.x - m1.x, m0.y - m1.y)
    assert abs(dist - 20.0) < 0.5


def test_hook_g1_stem_and_tip() -> None:
    from typekernel.geo.segment import CubicSegment

    frag = hook(0.0, 0.0, tip=(-20.0, 30.0), depth=12.0, tension=0.55)
    assert frag.start == Point(0.0, 0.0)
    assert frag.end == Point(-20.0, 30.0)
    stem = LineSegment(Point(0, -10), Point(0, 0))
    assert g1_join_error(stem, frag.segments[0]) < 1e-6
    assert isinstance(frag.segments[0], CubicSegment)
    assert isinstance(frag.segments[1], CubicSegment)
    belly_pt = frag.segments[0].p3
    assert math.isclose(belly_pt.x, -12.0, abs_tol=1e-9)
    assert math.isclose(belly_pt.y, 15.0, abs_tol=1e-9)
    # Default tip tangent curls back toward the stem (+x here).
    et = frag.end_tangent()
    assert et.x > 0 and abs(et.y) < 1e-6
    assert g1_join_error(frag.segments[0], frag.segments[1]) < 1e-6


def test_hook_rejects_same_y() -> None:
    try:
        hook(0.0, 10.0, tip=(-5.0, 10.0), depth=4.0)
    except ValueError as exc:
        assert "tip.y" in str(exc)
    else:
        raise AssertionError("expected ValueError")
