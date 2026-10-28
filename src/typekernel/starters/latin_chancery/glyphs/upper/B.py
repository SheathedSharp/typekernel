"""Uppercase B — stem + two nest bowls."""
from __future__ import annotations

from elements import nest_bowl, stroke

from typekernel.project import glyph
from typekernel.system import System


@glyph("B", group="uc.round")
def B(system: System):
    uc = float(system.stem["uc"])
    cap = float(system.zones.cap)
    width = float(system.tokens.get("B_width", 520.0))
    lsb = float(system.tokens.get("lsb_uc", 40.0))
    x0 = lsb + uc * 0.5
    stem = stroke(system, [(x0, 0.0), (x0, cap)], thickness=uc)
    top = nest_bowl(
        system, stem_x=x0, side="right", width=width * 0.85, xh=cap * 0.48,
        lsb=lsb, thickness=uc * 0.92, cy=cap * 0.72, rx=width * 0.28, ry=cap * 0.22, pull=0.78,
    )
    bot = nest_bowl(
        system, stem_x=x0, side="right", width=width, xh=cap * 0.55,
        lsb=lsb, thickness=uc * 0.92, cy=cap * 0.28, rx=width * 0.32, ry=cap * 0.26, pull=0.78,
    )
    return stem + top + bot
