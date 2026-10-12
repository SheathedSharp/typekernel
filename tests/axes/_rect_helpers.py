"""Synthetic rectangle outlines for axes tests."""

from __future__ import annotations

from typekernel.geo.contour import Contour
from typekernel.geo.outline import Outline
from typekernel.geo.point import Point
from typekernel.geo.segment import LineSegment


def closed_rect(x0: float, y0: float, x1: float, y1: float) -> Outline:
    """Axis-aligned closed rectangle as four line segments."""
    p00 = Point(x0, y0)
    p10 = Point(x1, y0)
    p11 = Point(x1, y1)
    p01 = Point(x0, y1)
    segments = (
        LineSegment(p00, p10),
        LineSegment(p10, p11),
        LineSegment(p11, p01),
        LineSegment(p01, p00),
    )
    contour = Contour(segments, closed=True)
    contour.assert_closed_consistent()
    contour.assert_segments_continuous()
    return Outline((contour,))
