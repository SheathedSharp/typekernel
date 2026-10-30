"""K — stem + mild arm/leg (interpolation-safe; acute join self-intersection)."""

from __future__ import annotations

from elements import WIDTHS, fuse, stroke, uc_stem

from typekernel.project import glyph
from typekernel.system import System


@glyph("K", group="uc.diag")
def K(system: System):
    uc = float(system.stem["uc"])
    cap = float(system.zones.cap)
    width = float(WIDTHS.get("K", 580.0))
    lsb = float(system.tokens.get("lsb_uc", 40.0))
    x0 = lsb + uc * 0.5
    x1 = lsb + width - uc * 0.25
    rise = 0.18
    return fuse(
        uc_stem(system, x0, thickness=uc)
        + stroke(system, [(x0, cap * (0.5 + rise)), (x1, cap)], thickness=uc)
        + stroke(system, [(x0, cap * (0.5 - rise)), (x1, 0.0)], thickness=uc)
    )
