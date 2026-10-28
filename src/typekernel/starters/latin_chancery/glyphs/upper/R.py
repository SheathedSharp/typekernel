"""Uppercase R — P + leg."""
from __future__ import annotations

from elements import nest_bowl, stroke

from typekernel.project import glyph
from typekernel.system import System


@glyph("R", group="uc.round")
def R(system: System):
    uc = float(system.stem["uc"])
    cap = float(system.zones.cap)
    width = float(system.tokens.get("R_width", 540.0))
    lsb = float(system.tokens.get("lsb_uc", 40.0))
    x0 = lsb + uc * 0.5
    x1 = lsb + width - uc * 0.2
    stem = stroke(system, [(x0, 0.0), (x0, cap)], thickness=uc)
    bowl = nest_bowl(
        system, stem_x=x0, side="right", width=width * 0.9, xh=cap * 0.55,
        lsb=lsb, thickness=uc, cy=cap * 0.68, rx=width * 0.3, ry=cap * 0.28, pull=0.72,
    )
    leg = stroke(system, [(x0 + uc * 0.3, cap * 0.42), (x1, 0.0)], thickness=uc)
    return stem + bowl + leg
