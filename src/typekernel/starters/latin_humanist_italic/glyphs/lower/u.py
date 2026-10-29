"""n-group glyph u — stems + shallow bottom (G-class; deep U SI under pen)."""

from __future__ import annotations

import math

from elements import stroke

from typekernel.project import glyph
from typekernel.system import System


@glyph("u", group="lc.straight")
def u(system: System):
    st = float(system.stem["lc"])
    xh = float(system.zones.x)
    width = float(system.tokens["n_width"])
    lsb = float(system.tokens.get("lsb_lc", 36.0))
    x0 = lsb + st * 0.5
    x1 = lsb + width - st * 0.5
    left = stroke(system, [(x0, xh), (x0, xh * 0.35)], thickness=st)
    right = stroke(system, [(x1, xh * 0.35), (x1, xh)], thickness=st)
    # Shallow sine bottom — deep mirrored-n arches self-intersect under slanted pen.
    n = 8
    ry = (x1 - x0) * 0.5 * 0.12
    pts = []
    for i in range(n + 1):
        t = i / n
        pts.append((x0 + (x1 - x0) * t, ry * math.sin(math.pi * t)))
    bottom = stroke(system, pts, thickness=st)
    return left + bottom + right
