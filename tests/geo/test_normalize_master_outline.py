"""VF master outline normalisation."""

from __future__ import annotations

from typekernel.geo.contour import Contour
from typekernel.geo.outline import Outline, normalize_master_outline
from typekernel.geo.point import Point
from typekernel.geo.segment import CubicSegment, LineSegment


def test_normalize_master_outline_converts_lines_and_sorts() -> None:
    line_ct = Contour(
        (
            LineSegment(Point(0.0, 10.0), Point(40.0, 10.0)),
            LineSegment(Point(40.0, 10.0), Point(40.0, 50.0)),
            LineSegment(Point(40.0, 50.0), Point(0.0, 50.0)),
            LineSegment(Point(0.0, 50.0), Point(0.0, 10.0)),
        ),
        closed=True,
    )
    cubic_ct = Contour(
        (
            CubicSegment(
                Point(0.0, 0.0),
                Point(10.0, 0.0),
                Point(20.0, 0.0),
                Point(30.0, 0.0),
            ),
        ),
        closed=True,
    )
    out = normalize_master_outline(Outline((cubic_ct, line_ct)))
    assert all(seg.kind == "cubic" for ct in out.contours for seg in ct.segments)
    assert out.contours[0].segments[0].points[0].y <= out.contours[1].segments[0].points[0].y
