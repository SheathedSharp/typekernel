"""N — continuous left stem + diagonal + right stem."""

from __future__ import annotations

from elements import stroke

from typekernel.project import glyph
from typekernel.system import System


@glyph("N", group="uc.straight")
def N(system: System):
    uc = float(system.stem["uc"])
    cap = float(system.zones.cap)
    width = float(system.tokens.get("N_width", 600.0))
    lsb = float(system.tokens.get("lsb_uc", 44.0))
    x0 = lsb + uc * 0.5
    x1 = lsb + width - uc * 0.5
    return stroke(
        system,
        [(x0, 0.0), (x0, cap), (x1, 0.0), (x1, cap)],
        thickness=uc,
    )
