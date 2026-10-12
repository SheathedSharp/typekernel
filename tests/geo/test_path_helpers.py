"""Tests for cubic path helpers and PathBuilder convenience methods."""

from __future__ import annotations

import math

import pytest

from typekernel.geo.path_builder import PathBuilder
from typekernel.geo.path_helpers import (
    KAPPA,
    arc_cubics,
    ellipse_cubics,
    quarter_circle_cubics,
    rounded_corner_cubics,
    smooth_cubic_controls,
)
from typekernel.geo.point import Point
from typekernel.geo.segment import CubicSegment
from typekernel.geo.smoothness import assert_g1_join, g1_join_error, is_g1_join


def test_kappa_documented_constant() -> None:
    assert abs(KAPPA - 4.0 / 3.0 * math.tan(math.pi / 8.0)) < 1e-12


def test_quarter_circle_endpoints() -> None:
    p0, _, _, p3 = quarter_circle_cubics(0, 0, 100, 100, 0)
    assert p0 == Point(100, 0)
    assert p3 == Point(0, 100)


def test_ellipse_closed_four_quarters() -> None:
    cubics = ellipse_cubics(50, 50, 40, 30)
    assert len(cubics) == 4
    assert cubics[0][0] == Point(90, 50)
    assert cubics[-1][3] == Point(90, 50)


def test_arc_cubics_full_circle_four_segments() -> None:
    cubics = arc_cubics(0, 0, 10, 10, 0, 360)
    assert len(cubics) == 4
    assert cubics[0][0] == Point(10, 0)


def test_pathbuilder_add_ellipse() -> None:
    b = PathBuilder()
    b.addEllipse(0, 0, 20, 10)
    outline = b.build()
    assert outline.contour_count == 1
    assert all(isinstance(s, CubicSegment) for s in outline.contours[0].segments)


def test_pathbuilder_quarter_and_rounded() -> None:
    b = PathBuilder()
    b.moveTo(100, 0)
    b.quarterCircleTo(0, 0, 100, 100, 0)
    assert b.build().contours[0].segments[-1].p3 == Point(0, 100)

    b2 = PathBuilder()
    b2.moveTo(0, 0)
    b2.roundedCornerTo(100, 0, 100, 100, 20)
    segs = b2.build().contours[0].segments
    assert any(isinstance(s, CubicSegment) for s in segs)


def test_rounded_corner_rejects_negative_radius() -> None:
    with pytest.raises(ValueError, match="radius"):
        rounded_corner_cubics(Point(0, 0), Point(1, 0), Point(1, 1), -1)


def test_smooth_controls_and_g1() -> None:
    p0, p3 = Point(0, 0), Point(100, 0)
    p1, p2 = smooth_cubic_controls(p0, p3, Point(1, 0), Point(1, 0))
    seg = CubicSegment(p0, p1, p2, p3)
    # Self-join with an identical continuation direction.
    seg2 = CubicSegment(p3, Point(p3.x + 30, p3.y), Point(p3.x + 70, p3.y), Point(200, 0))
    assert is_g1_join(seg, seg2)
    assert g1_join_error(seg, seg2) < 1e-9
    assert_g1_join(seg, seg2)


def test_smooth_curve_to_on_builder() -> None:
    b = PathBuilder()
    b.moveTo(0, 0)
    b.lineTo(50, 0)
    b.smoothCurveTo(100, 50, tangent_out_x=0, tangent_out_y=1)
    outline = b.build()
    assert len(outline.contours[0].segments) == 2
    assert isinstance(outline.contours[0].segments[1], CubicSegment)
