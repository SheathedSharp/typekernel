"""Figure 3 — two stacked open arcs (skeleton+pen)."""

from __future__ import annotations

from elements import open_arc_points, stroke

from typekernel.project import glyph
from typekernel.system import System


@glyph("three", group="figs")
def three(system: System):
    st = float(system.stem["lc"])
    width = float(system.tokens.get("fig_width", 460.0))
    lsb = float(system.tokens.get("lsb_lc", 36.0))
    h = float(system.zones.cap) * 0.72
    cx = lsb + width * 0.42
    upper = open_arc_points(cx, h * 0.70, width * 0.40, h * 0.26, start_deg=160.0, end_deg=-20.0, n=14)
    lower = open_arc_points(cx, h * 0.28, width * 0.42, h * 0.30, start_deg=20.0, end_deg=-160.0, n=14)
    return stroke(system, list(upper) + list(lower), thickness=st)
