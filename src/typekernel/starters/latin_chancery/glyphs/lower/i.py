"""Lowercase i — stem + pen_dot tittle (demo of shared dot helper)."""

from __future__ import annotations

from elements import pen_dot, stroke

from typekernel.project import glyph
from typekernel.system import System


@glyph("i", group="lc.straight")
def i(system: System):
    st = float(system.stem["lc"])
    xh = float(system.zones.x)
    lsb = float(system.tokens.get("lsb_lc", 32.0))
    x = lsb + st * 0.5
    stem = stroke(system, [(x, 0.0), (x, xh)], thickness=st)
    r = float(system.tokens["dot_radius"])
    cy = xh + float(system.overshoot.round) + r * 1.2
    return stem + pen_dot(system, x, cy, radius=r)
