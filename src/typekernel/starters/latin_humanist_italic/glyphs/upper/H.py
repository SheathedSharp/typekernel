"""Control glyph H — three slanted strokes (stems + bar) overlaid."""

from __future__ import annotations

from elements import stroke

from typekernel.project import glyph
from typekernel.system import System


@glyph("H", group="control")
def H(system: System):
    uc = float(system.stem["uc"])
    cap = float(system.zones.cap)
    width = float(system.tokens["H_width"])
    lsb = float(system.tokens.get("lsb_uc", 44.0))
    bar_y = cap * 0.48
    x_l = lsb + uc * 0.5
    x_r = lsb + width - uc * 0.5
    left = stroke(system, [(x_l, 0.0), (x_l, cap)], thickness=uc)
    right = stroke(system, [(x_r, 0.0), (x_r, cap)], thickness=uc)
    bar = stroke(
        system,
        [(x_l, bar_y), (x_r, bar_y)],
        thickness=uc * 0.85,
    )
    return left + right + bar
