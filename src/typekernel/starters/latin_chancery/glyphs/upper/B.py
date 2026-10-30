"""B — stem + three bars (interpolation-safe; dual bowls self-intersection under chancery pen)."""

from __future__ import annotations

from elements import WIDTHS, fuse, stroke, uc_stem

from typekernel.project import glyph
from typekernel.system import System


@glyph("B", group="uc.round")
def B(system: System):
    uc = float(system.stem["uc"])
    cap = float(system.zones.cap)
    width = float(WIDTHS.get("B", 580.0))
    lsb = float(system.tokens.get("lsb_uc", 40.0))
    x0 = lsb + uc * 0.5
    return fuse(
        uc_stem(system, x0, thickness=uc)
        + stroke(system, [(x0, cap), (lsb + width, cap)], thickness=uc)
        + stroke(system, [(x0, cap * 0.5), (lsb + width * 0.85, cap * 0.5)], thickness=uc)
        + stroke(system, [(x0, 0.0), (lsb + width, 0.0)], thickness=uc)
    )
