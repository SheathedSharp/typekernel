"""Uppercase D — stem + nest bowl."""
from __future__ import annotations

from elements import nest_bowl, stroke

from typekernel.project import glyph
from typekernel.system import System


@glyph("D", group="uc.round")
def D(system: System):
    uc = float(system.stem["uc"])
    cap = float(system.zones.cap)
    width = float(system.tokens.get("D_width", 560.0))
    lsb = float(system.tokens.get("lsb_uc", 40.0))
    x0 = lsb + uc * 0.5
    stem = stroke(system, [(x0, 0.0), (x0, cap)], thickness=uc)
    bowl = nest_bowl(
        system, stem_x=x0, side="right", width=width, xh=cap,
        lsb=lsb, thickness=uc * 0.95, cy=cap * 0.5, rx=width * 0.4, ry=cap * 0.47, pull=0.82,
    )
    return stem + bowl
