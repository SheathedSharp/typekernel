"""M — outer stems + inner diagonals (skeleton+pen)."""

from __future__ import annotations

from elements import stroke

from typekernel.project import glyph
from typekernel.system import System


@glyph("M", group="uc.straight")
def M(system: System):
    uc = float(system.stem["uc"])
    cap = float(system.zones.cap)
    width = float(system.tokens.get("M_width", 760.0))
    lsb = float(system.tokens.get("lsb_uc", 44.0))
    x0 = lsb + uc * 0.5
    x3 = lsb + width - uc * 0.5
    mid = (x0 + x3) / 2.0
    left = stroke(system, [(x0, 0.0), (x0, cap)], thickness=uc)
    right = stroke(system, [(x3, 0.0), (x3, cap)], thickness=uc)
    d1 = stroke(system, [(x0, cap), (mid, 0.0)], thickness=uc)
    d2 = stroke(system, [(x3, cap), (mid, 0.0)], thickness=uc)
    return left + right + d1 + d2
