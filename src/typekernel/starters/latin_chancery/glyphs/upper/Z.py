"""Z — fused bars + diagonal (interpolation-safe)."""

from __future__ import annotations

from elements import fuse, stroke

from typekernel.project import glyph
from typekernel.system import System


@glyph("Z", group="uc.diag")
def Z(system: System):
    uc = float(system.stem["uc"])
    cap = float(system.zones.cap)
    width = float(system.tokens.get("Z_width", 560.0))
    lsb = float(system.tokens.get("lsb_uc", 40.0))
    x0, x1 = lsb, lsb + width
    return fuse(
        stroke(system, [(x0, cap), (x1, cap), (x0, 0.0), (x1, 0.0)], thickness=uc)
    )
