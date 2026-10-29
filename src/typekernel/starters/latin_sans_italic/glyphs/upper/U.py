"""U — stems + shallow cup (P5-3)."""

from __future__ import annotations

import math

from elements import stroke

from typekernel.project import glyph
from typekernel.system import System


@glyph("U", group="uc.straight")
def U(system: System):
    st = float(system.stem["uc"])
    cap = float(system.zones.cap)
    width = float(system.tokens.get("U_width", 620.0))
    lsb = float(system.tokens["lsb_uc"])
    x0 = lsb + st * 0.5
    x1 = lsb + width - st * 0.5
    left = stroke(system, [(x0, cap), (x0, cap * 0.35)], thickness=st)
    right = stroke(system, [(x1, cap * 0.35), (x1, cap)], thickness=st)
    n = 8
    ry = (x1 - x0) * 0.5 * 0.12
    pts = [(x0 + (x1 - x0) * i / n, ry * math.sin(math.pi * i / n)) for i in range(n + 1)]
    bottom = stroke(system, pts, thickness=st)
    return left + bottom + right
