"""Lowercase j — descender stem + pen_dot + fixed arc hook."""
from __future__ import annotations
from elements import open_arc_points, pen_dot, stroke
from typekernel.project import glyph
from typekernel.system import System

@glyph("j", group="lc.straight")
def j(system: System):
    st = float(system.stem["lc"])
    xh = float(system.zones.x)
    desc = float(system.zones.desc)
    lsb = float(system.tokens.get("lsb_lc", 32.0))
    x = lsb + st * 1.2
    stem = stroke(system, [(x, xh), (x, desc + 70.0)], thickness=st)
    r = float(system.tokens["dot_radius"])
    cy = xh + float(system.overshoot.round) + r * 1.2
    hook = stroke(
        system,
        open_arc_points(x - 55.0, desc + 55.0, 70.0, 55.0, start_deg=10, end_deg=200, n=20),
        thickness=float(system.stem["lc_h"]),
    )
    return stem + pen_dot(system, x, cy, radius=r) + hook
