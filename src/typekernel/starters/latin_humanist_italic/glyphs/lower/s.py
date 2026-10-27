"""s — stacked open arcs overlapping at the waist (skeleton+pen)."""

from __future__ import annotations

from elements import open_arc_points, stroke

from typekernel.project import glyph
from typekernel.system import System


@glyph("s", group="lc.round")
def s(system: System):
    st = float(system.stem["lc"])
    xh = float(system.zones.x)
    width = float(system.tokens.get("s_width", 360.0))
    lsb = float(system.tokens.get("lsb_lc", 36.0))
    ov = float(system.overshoot.round)
    cx = lsb + width / 2.0
    rx = width / 2.0 * 0.92
    ry = xh * 0.30
    # Upper bowl open on the right; lower open on the left — continuous S path.
    upper = open_arc_points(cx, (xh + ov) - ry, rx, ry, start_deg=40.0, end_deg=220.0, n=18)
    lower = open_arc_points(cx, (-ov) + ry, rx, ry, start_deg=40.0, end_deg=-140.0, n=18)
    # One continuous skeleton: upper then lower (share waist).
    pts = list(upper) + list(lower)
    return stroke(system, pts, thickness=st)
