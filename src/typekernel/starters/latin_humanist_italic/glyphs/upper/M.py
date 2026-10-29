"""M — outer uc stems + per-leg compensated diagonal valley."""

from __future__ import annotations

from elements import diagonal_stroke, fuse, uc_stem

from typekernel.project import glyph
from typekernel.system import System


@glyph("M", group="uc.straight")
def M(system: System):
    uc = float(system.stem["uc"])
    cap = float(system.zones.cap)
    width = float(system.tokens.get("M_width", 760.0))
    lsb = float(system.tokens.get("lsb_uc", 44.0))
    x0 = lsb + uc * 0.5
    x3 = lsb + width - uc * 0.5
    mid = (x0 + x3) / 2.0
    left = uc_stem(system, x0, thickness=uc)
    right = uc_stem(system, x3, thickness=uc)
    valley = (
        diagonal_stroke(system, [(x0, cap), (mid, 0.0)], thickness=uc)
        + diagonal_stroke(system, [(mid, 0.0), (x3, cap)], thickness=uc)
    )
    return fuse(left + valley + right)
