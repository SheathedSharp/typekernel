"""C — open capital oval (skeleton+pen)."""

from __future__ import annotations

from elements import open_arc_points, stroke

from typekernel.project import glyph
from typekernel.system import System


@glyph("C", group="uc.round")
def C(system: System):
    uc = float(system.stem["uc"])
    cap = float(system.zones.cap)
    width = float(system.tokens.get("O_width", 620.0)) * 0.95
    lsb = float(system.tokens.get("lsb_uc", 44.0))
    ov = float(system.overshoot.round)
    cx = lsb + width / 2.0
    cy = cap / 2.0
    rx = width / 2.0 - uc * 0.1
    ry = cap / 2.0 + ov - uc * 0.1
    pts = open_arc_points(cx, cy, rx, ry, start_deg=35.0, end_deg=325.0, n=28)
    return stroke(system, pts, thickness=uc)
