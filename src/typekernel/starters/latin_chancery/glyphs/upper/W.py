"""W — fused double-V (interpolation-safe)."""

from __future__ import annotations

from elements import WIDTHS, fuse, stroke

from typekernel.project import glyph
from typekernel.system import System


@glyph("W", group="uc.diag")
def W(system: System):
    uc = float(system.stem["uc"])
    cap = float(system.zones.cap)
    width = float(WIDTHS.get("W", 900.0))
    lsb = float(system.tokens.get("lsb_uc", 40.0))
    x0 = lsb + uc * 0.2
    x3 = lsb + width - uc * 0.2
    x1 = lsb + width * 0.35
    x2 = lsb + width * 0.65
    return fuse(
        stroke(
            system,
            [(x0, cap), (x1, cap * 0.12), ((x1 + x2) / 2.0, cap * 0.55), (x2, cap * 0.12), (x3, cap)],
            thickness=uc,
        )
    )
