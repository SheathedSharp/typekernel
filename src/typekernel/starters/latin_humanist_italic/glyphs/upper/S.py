"""S — stacked open arcs (skeleton+pen)."""

from __future__ import annotations

from elements import open_arc_points, stroke

from typekernel.project import glyph
from typekernel.system import System


@glyph("S", group="uc.round")
def S(system: System):
    uc = float(system.stem["uc"])
    cap = float(system.zones.cap)
    width = float(system.tokens.get("S_width", 540.0))
    lsb = float(system.tokens.get("lsb_uc", 44.0))
    ov = float(system.overshoot.round)
    cx = lsb + width / 2.0
    rx = width / 2.0 * 0.92
    ry = cap * 0.28
    upper = open_arc_points(cx, (cap + ov) - ry, rx, ry, start_deg=40.0, end_deg=220.0, n=18)
    lower = open_arc_points(cx, (-ov) + ry, rx, ry, start_deg=40.0, end_deg=-140.0, n=18)
    return stroke(system, list(upper) + list(lower), thickness=uc)
