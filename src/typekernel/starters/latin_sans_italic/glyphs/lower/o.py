"""Control o — closed oval via polyline expand."""

from __future__ import annotations

import math

from elements import stroke

from typekernel.project import glyph
from typekernel.system import System


@glyph("o", group="control")
def o(system: System):
    st = float(system.stem["lc"])
    xh = float(system.zones.x)
    width = float(system.tokens["o_width"])
    lsb = float(system.tokens["lsb_lc"])
    ov = float(system.overshoot.round)
    cx = lsb + width / 2.0
    cy = xh / 2.0
    rx = width / 2.0 - st * 0.15
    ry = xh / 2.0 + ov * 0.5 - st * 0.15
    n = 64
    pts = [
        (cx + rx * math.cos(2 * math.pi * i / n), cy + ry * math.sin(2 * math.pi * i / n))
        for i in range(n)
    ]
    return stroke(system, pts, closed=True, thickness=st)
