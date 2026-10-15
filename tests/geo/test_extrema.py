"""TK-402: cubic axis-extrema splitting (draw-time rebalance helper)."""

from __future__ import annotations

from typekernel.geo.contour import Contour
from typekernel.geo.extrema import outline_with_axis_extrema_on_curve
from typekernel.geo.outline import Outline
from typekernel.geo.point import Point
from typekernel.geo.segment import CubicSegment


def test_split_cubic_puts_on_curve_at_vertical_extremum() -> None:
    # Horizontal cubic with interior ymax not at endpoints.
    seg = CubicSegment(
        Point(0.0, 0.0),
        Point(40.0, 120.0),
        Point(60.0, 120.0),
        Point(100.0, 0.0),
    )
    out = outline_with_axis_extrema_on_curve(Outline((Contour((seg,), closed=False),)))
    parts = [s for s in out.iter_segments() if isinstance(s, CubicSegment)]
    assert len(parts) == 2
    ys = {p.y for seg in parts for p in seg.points}
    assert max(ys) in {p.y for seg in parts for p in (seg.p0, seg.p3)}
