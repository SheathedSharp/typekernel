"""Y — continuous left-arm+stem rail + right arm to shared join."""

from __future__ import annotations

from elements import stroke

from typekernel.project import glyph
from typekernel.system import System


@glyph("Y", group="uc.diag")
def Y(system: System):
    uc = float(system.stem["uc"])
    cap = float(system.zones.cap)
    width = float(system.tokens.get("Y_width", 600.0))
    lsb = float(system.tokens.get("lsb_uc", 44.0))
    x0 = lsb + uc * 0.2
    x1 = lsb + width - uc * 0.2
    mid = (x0 + x1) / 2.0
    join = cap * 0.42
    left = stroke(system, [(x0, cap), (mid, join), (mid, 0.0)], thickness=uc)
    right = stroke(system, [(x1, cap), (mid, join)], thickness=uc)
    return left + right
