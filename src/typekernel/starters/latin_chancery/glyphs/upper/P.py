"""Uppercase P — stem + upper bowl."""
from __future__ import annotations
from elements import nest_bowl, stroke
from typekernel.project import glyph
from typekernel.system import System

@glyph("P", group="uc.round")
def P(system: System):
    uc = float(system.stem["uc"])
    cap = float(system.zones.cap)
    width = float(system.tokens.get("P_width", 500.0))
    lsb = float(system.tokens.get("lsb_uc", 40.0))
    x0 = lsb + uc * 0.5
    stem = stroke(system, [(x0, 0.0), (x0, cap)], thickness=uc)
    bowl = nest_bowl(
        system, stem_x=x0, side="right", width=width, xh=cap * 0.55,
        lsb=lsb, thickness=uc, cy=cap * 0.68, rx=width * 0.32, ry=cap * 0.28, pull=0.72,
    )
    return stem + bowl
