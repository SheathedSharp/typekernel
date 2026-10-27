"""W — continuous double-V rail (shared peaks/valleys)."""

from __future__ import annotations

from elements import stroke

from typekernel.project import glyph
from typekernel.system import System


@glyph("W", group="uc.diag")
def W(system: System):
    uc = float(system.stem["uc"])
    cap = float(system.zones.cap)
    width = float(system.tokens.get("W_width", 900.0))
    lsb = float(system.tokens.get("lsb_uc", 44.0))
    x0 = lsb + uc * 0.2
    x3 = lsb + width - uc * 0.2
    x1 = lsb + width * 0.35
    x2 = lsb + width * 0.65
    mid = (x1 + x2) / 2.0
    return stroke(
        system,
        [(x0, cap), (x1, 0.0), (mid, cap * 0.55), (x2, 0.0), (x3, cap)],
        thickness=uc,
    )
