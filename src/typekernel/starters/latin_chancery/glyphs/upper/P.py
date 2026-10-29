"""P — stem + top/mid bars (G-class; nest bowl SI)."""

from __future__ import annotations

from elements import fuse, stroke, uc_stem

from typekernel.project import glyph
from typekernel.system import System


@glyph("P", group="uc.round")
def P(system: System):
    uc = float(system.stem["uc"])
    cap = float(system.zones.cap)
    width = float(system.tokens.get("P_width", 540.0))
    lsb = float(system.tokens.get("lsb_uc", 40.0))
    x0 = lsb + uc * 0.5
    return fuse(
        uc_stem(system, x0, thickness=uc)
        + stroke(system, [(x0, cap), (lsb + width, cap)], thickness=uc)
        + stroke(system, [(x0, cap * 0.5), (lsb + width * 0.85, cap * 0.5)], thickness=uc)
    )
