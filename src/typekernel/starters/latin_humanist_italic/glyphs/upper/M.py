"""M — continuous outer stems + inner diagonals as one rail."""

from __future__ import annotations

from elements import stroke

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
    # Left stem up → valley → right stem down (continuous joins at peaks).
    return stroke(
        system,
        [(x0, 0.0), (x0, cap), (mid, 0.0), (x3, cap), (x3, 0.0)],
        thickness=uc,
    )
