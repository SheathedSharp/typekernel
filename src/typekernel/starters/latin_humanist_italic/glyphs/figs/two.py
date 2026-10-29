"""Figure 2 — continuous open top into diagonal and baseline."""

from __future__ import annotations

from elements import open_arc_points, stroke

from typekernel.project import glyph
from typekernel.system import System


@glyph("two", group="figs")
def two(system: System):
    st = float(system.stem["lc"])
    width = float(system.tokens.get("fig_width", 460.0))
    lsb = float(system.tokens.get("lsb_lc", 36.0))
    h = float(system.zones.cap) * 0.72
    cx = lsb + width / 2.0
    top = open_arc_points(
        cx, h * 0.68, width * 0.38, h * 0.28, start_deg=200.0, end_deg=10.0, n=18
    )
    end = top[-1]
    pts = list(top) + [
        (lsb + width * 0.88, h * 0.42),
        (lsb + width * 0.12, 0.0),
        (lsb + width * 0.88, 0.0),
    ]
    pts[len(top)] = (max(end[0], lsb + width * 0.75), min(end[1], h * 0.50))
    return stroke(system, pts, thickness=st)
