"""Y — fused arms into stem ."""

from __future__ import annotations

from elements import WIDTHS, fuse, stroke

from typekernel.project import glyph
from typekernel.system import System


@glyph("Y", group="uc.diag")
def Y(system: System):
    uc = float(system.stem["uc"])
    cap = float(system.zones.cap)
    width = float(WIDTHS.get("Y", 620.0))
    lsb = float(system.tokens["lsb_uc"])
    x0 = lsb + uc * 0.2
    x1 = lsb + width - uc * 0.2
    mid = (x0 + x1) / 2.0
    join = cap * 0.42
    return fuse(
        stroke(system, [(x0, cap), (mid, join), (mid, 0.0)], thickness=uc)
        + stroke(system, [(x1, cap), (mid, join)], thickness=uc)
    )
