"""J — stem + shallow hook (G-class)."""

from __future__ import annotations

import math

from elements import stroke

from typekernel.project import glyph
from typekernel.system import System


@glyph("J", group="uc.straight")
def J(system: System):
    uc = float(system.stem["uc"])
    cap = float(system.zones.cap)
    width = float(system.tokens.get("J_width", 480.0))
    lsb = float(system.tokens.get("lsb_uc", 40.0))
    x = lsb + width - uc * 0.5
    stem = stroke(system, [(x, cap), (x, uc * 1.6)], thickness=uc)
    pts = []
    for i in range(7):
        t = i / 6.0
        pts.append(
            (
                x - width * 0.35 * math.sin(math.pi * 0.5 * t),
                uc * 0.5 + uc * 1.1 * (1.0 - math.cos(math.pi * 0.5 * t)),
            )
        )
    return stem + stroke(system, pts, thickness=uc)
