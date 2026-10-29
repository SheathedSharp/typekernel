"""W — fused double-V diagonals (P5-3)."""

from __future__ import annotations

from elements import fuse, stroke

from typekernel.project import glyph
from typekernel.system import System


@glyph("W", group="uc.diag")
def W(system: System):
    uc = float(system.stem["uc"])
    cap = float(system.zones.cap)
    width = float(system.tokens.get("W_width", 920.0))
    lsb = float(system.tokens["lsb_uc"])
    x0 = lsb + uc * 0.2
    x3 = lsb + width - uc * 0.2
    x1 = lsb + width * 0.35
    x2 = lsb + width * 0.65
    mid = (x1 + x2) / 2.0
    return fuse(
        stroke(system, [(x0, cap), (x1, 0.0)], thickness=uc)
        + stroke(system, [(x1, 0.0), (mid, cap * 0.55)], thickness=uc)
        + stroke(system, [(mid, cap * 0.55), (x2, 0.0)], thickness=uc)
        + stroke(system, [(x2, 0.0), (x3, cap)], thickness=uc)
    )
