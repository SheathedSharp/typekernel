"""V — continuous diagonal rail through the baseline apex."""

from __future__ import annotations

from elements import stroke

from typekernel.project import glyph
from typekernel.system import System


@glyph("V", group="uc.diag")
def V(system: System):
    uc = float(system.stem["uc"])
    cap = float(system.zones.cap)
    width = float(system.tokens.get("V_width", 620.0))
    lsb = float(system.tokens.get("lsb_uc", 44.0))
    x0 = lsb + uc * 0.2
    x1 = lsb + width - uc * 0.2
    mid = (x0 + x1) / 2.0
    return stroke(system, [(x0, cap), (mid, 0.0), (x1, cap)], thickness=uc)
