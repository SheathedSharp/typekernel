"""Z — fused bars + diagonal ."""

from __future__ import annotations

from elements import WIDTHS, fuse, stroke

from typekernel.project import glyph
from typekernel.system import System


@glyph("Z", group="uc.diag")
def Z(system: System):
    uc = float(system.stem["uc"])
    cap = float(system.zones.cap)
    width = float(WIDTHS.get("Z", 580.0))
    lsb = float(system.tokens["lsb_uc"])
    x0, x1 = lsb, lsb + width
    return fuse(
        stroke(system, [(x0, cap), (x1, cap)], thickness=uc)
        + stroke(system, [(x1, cap), (x0, 0.0)], thickness=uc)
        + stroke(system, [(x0, 0.0), (x1, 0.0)], thickness=uc)
    )
