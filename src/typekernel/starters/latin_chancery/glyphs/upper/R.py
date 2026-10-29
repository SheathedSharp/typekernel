"""R — stem + bars + gapped leg (interpolation-safe)."""

from __future__ import annotations

from elements import fuse, stroke, uc_stem

from typekernel.project import glyph
from typekernel.system import System


@glyph("R", group="uc.round")
def R(system: System):
    uc = float(system.stem["uc"])
    cap = float(system.zones.cap)
    width = float(system.tokens.get("R_width", 600.0))
    lsb = float(system.tokens.get("lsb_uc", 40.0))
    x0 = lsb + uc * 0.5
    return fuse(
        uc_stem(system, x0, thickness=uc)
        + stroke(system, [(x0, cap), (lsb + width, cap)], thickness=uc)
        + stroke(system, [(x0, cap * 0.5), (lsb + width * 0.85, cap * 0.5)], thickness=uc)
    ) + stroke(
        system, [(lsb + width * 0.55, cap * 0.35), (lsb + width - uc * 0.2, 0.0)], thickness=uc
    )
