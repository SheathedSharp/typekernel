"""Uppercase K — stem + arms."""
from __future__ import annotations
from elements import stroke
from typekernel.project import glyph
from typekernel.system import System

@glyph("K", group="uc.diag")
def K(system: System):
    uc = float(system.stem["uc"])
    cap = float(system.zones.cap)
    width = float(system.tokens.get("K_width", 520.0))
    lsb = float(system.tokens.get("lsb_uc", 40.0))
    x0 = lsb + uc * 0.5
    x1 = lsb + width - uc * 0.2
    join = cap * 0.45
    stem = stroke(system, [(x0, 0.0), (x0, cap)], thickness=uc)
    upper = stroke(system, [(x0 + uc * 0.2, join), (x1, cap)], thickness=uc)
    lower = stroke(system, [(x0 + uc * 0.2, join), (x1, 0.0)], thickness=uc)
    return stem + upper + lower
