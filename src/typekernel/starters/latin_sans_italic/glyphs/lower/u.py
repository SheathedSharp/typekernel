"""n-group glyph u — stems + shallow cup."""

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
    lsb = float(system.tokens["lsb_lc"])
    x0 = lsb + st * 0.5
    x1 = lsb + width - st * 0.5
    left = stroke(system, [(x0, xh), (x0, xh * 0.35)], thickness=st)
    right = stroke(system, [(x1, xh * 0.35), (x1, xh)], thickness=st)
    n = 8
    ry = (x1 - x0) * 0.5 * 0.12
    pts = [(x0 + (x1 - x0) * i / n, ry * math.sin(math.pi * i / n)) for i in range(n + 1)]
    bottom = stroke(system, pts, thickness=st)
    return left + bottom + right
