"""Round glyph c — open oval aperture on the right (skeleton+pen)."""

from __future__ import annotations

from elements import open_arc_points, stroke

from typekernel.project import glyph
from typekernel.system import System


@glyph("c", group="lc.round")
def c(system: System):
    st = float(system.stem["lc"])
    xh = float(system.zones.x)
    width = float(system.tokens.get("o_width", 420.0)) * 0.95
    lsb = float(system.tokens.get("lsb_lc", 36.0))
    ov = float(system.overshoot.round)
    cx = lsb + width / 2.0
    cy = xh / 2.0
    rx = width / 2.0 - st * 0.1
    ry = xh / 2.0 + ov * 0.5 - st * 0.1
    # Open on the right: arc from ~40° to ~320° CCW (skip east aperture).
    pts = open_arc_points(cx, cy, rx, ry, start_deg=40.0, end_deg=320.0, n=24)
    return stroke(system, pts, thickness=st)
