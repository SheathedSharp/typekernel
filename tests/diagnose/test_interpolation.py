"""P2-9: interpolation fixtures — start mismatch, mid self-intersect."""

from __future__ import annotations

import pytest

from typekernel.diagnose.checks.interpolation import lerp_outline
from typekernel.geo.contour import Contour
from typekernel.geo.outline import Outline
from typekernel.geo.point import Point
from typekernel.geo.segment import LineSegment


def _sq(x0, y0, x1, y1) -> Contour:
    return Contour(
        (
            LineSegment(Point(x0, y0), Point(x1, y0)),
            LineSegment(Point(x1, y0), Point(x1, y1)),
            LineSegment(Point(x1, y1), Point(x0, y1)),
            LineSegment(Point(x0, y1), Point(x0, y0)),
        ),
        closed=True,
    )


def test_lerp_outline_midpoint() -> None:
    a = Outline((_sq(0, 0, 100, 100),))
    b = Outline((_sq(0, 0, 200, 200),))
    mid = lerp_outline(a, b, 0.5)
    # Top-right corner ~ (150, 150)
    pts = mid.contours[0].segments[1].points
    assert abs(pts[1].x - 150) < 1e-6


def test_start_mismatch_raises() -> None:
    a = Outline((_sq(0, 0, 100, 100),))
    # Different segment count
    b = Outline(
        (
            Contour(
                (
                    LineSegment(Point(0, 0), Point(100, 0)),
                    LineSegment(Point(100, 0), Point(100, 100)),
                    LineSegment(Point(100, 100), Point(0, 0)),
                ),
                closed=True,
            ),
        )
    )
    with pytest.raises(ValueError, match="segment"):
        lerp_outline(a, b, 0.5)
