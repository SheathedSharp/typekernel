"""X — fused crossing diagonals (P5-3)."""

from __future__ import annotations

from elements import fuse, stroke

from typekernel.project import glyph
from typekernel.system import System


@glyph("X", group="uc.diag")
def X(system: System):
    uc = float(system.stem["uc"])
    cap = float(system.zones.cap)
    width = float(system.tokens.get("X_width", 620.0))
    lsb = float(system.tokens["lsb_uc"])
    x0 = lsb + uc * 0.2
    x1 = lsb + width - uc * 0.2
    cx = (x0 + x1) / 2.0
    cy = cap / 2.0
    return fuse(
        stroke(system, [(x0, cap), (cx, cy), (x1, 0.0)], thickness=uc)
        + stroke(system, [(x1, cap), (cx, cy), (x0, 0.0)], thickness=uc)
    )
