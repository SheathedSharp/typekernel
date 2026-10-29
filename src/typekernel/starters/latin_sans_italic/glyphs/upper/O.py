"""Control O — closed capital oval."""

from __future__ import annotations

import math

from elements import stroke

from typekernel.project import glyph
from typekernel.system import System


@glyph("O", group="control")
def O(system: System):
    st = float(system.stem["uc"])
    cap = float(system.zones.cap)
    width = float(system.tokens["O_width"])
    lsb = float(system.tokens["lsb_uc"])
    ov = float(system.overshoot.round)
    cx = lsb + width / 2.0
    cy = cap / 2.0
    rx = width / 2.0 - st * 0.15
    ry = cap / 2.0 + ov * 0.5 - st * 0.15
    n = 64
    pts = [
        (cx + rx * math.cos(2 * math.pi * i / n), cy + ry * math.sin(2 * math.pi * i / n))
        for i in range(n)
    ]
    return stroke(system, pts, closed=True, thickness=st)
