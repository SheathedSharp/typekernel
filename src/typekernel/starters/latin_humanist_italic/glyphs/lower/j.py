"""j — descender stem + shallow hook + oval tittle (interpolation-safe)."""

from __future__ import annotations

import math

from elements import oval_points, stroke

from typekernel.project import glyph
from typekernel.system import System


@glyph("j", group="lc.straight")
def j(system: System):
    st = float(system.stem["lc"])
    xh = float(system.zones.x)
    desc = float(system.zones.desc)
    lsb = float(system.tokens.get("lsb_lc", 36.0))
    x = lsb + st * 1.1
    stem = stroke(system, [(x, xh * 0.65), (x, desc + st * 1.4)], thickness=st)
    pts = []
    for i in range(7):
        t = i / 6.0
        pts.append(
            (
                x - st * 1.4 * math.sin(math.pi * 0.5 * t),
                (desc + st * 0.5) + st * 0.9 * (1.0 - math.cos(math.pi * 0.5 * t)),
            )
        )
    hook = stroke(system, pts, thickness=st)
    cy = xh * 0.88
    dot = stroke(
        system,
        oval_points(x, cy, st * 0.35, st * 0.4, n=12),
        closed=True,
        thickness=st * 0.35,
    )
    return stem + hook + dot
