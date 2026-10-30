"""Y — arms into stem with gap (interpolation-safe)."""

from __future__ import annotations

from elements import WIDTHS, fuse, stroke

from typekernel.project import glyph
from typekernel.system import System


@glyph("Y", group="uc.diag")
def Y(system: System):
    uc = float(system.stem["uc"])
    cap = float(system.zones.cap)
    width = float(WIDTHS.get("Y", 600.0))
    lsb = float(system.tokens.get("lsb_uc", 40.0))
    x0 = lsb + uc * 0.25
    x1 = lsb + width - uc * 0.25
    mid = (x0 + x1) / 2.0
    join = cap * 0.45
    return fuse(
        stroke(system, [(x0, cap), (mid, join)], thickness=uc)
        + stroke(system, [(x1, cap), (mid, join), (mid, 0.0)], thickness=uc)
    )
