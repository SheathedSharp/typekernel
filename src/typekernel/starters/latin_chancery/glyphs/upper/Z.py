"""Uppercase Z — zigzag."""
from __future__ import annotations
from elements import stroke
from typekernel.project import glyph
from typekernel.system import System

@glyph("Z", group="uc.diag")
def Z(system: System):
    uc = float(system.stem["uc"])
    cap = float(system.zones.cap)
    width = float(system.tokens.get("Z_width", 520.0))
    lsb = float(system.tokens.get("lsb_uc", 40.0))
    x0 = lsb + uc * 0.15
    x1 = lsb + width - uc * 0.15
    thin = float(system.stem["uc_h"])
    return (
        stroke(system, [(x0, cap), (x1, cap)], thickness=thin)
        + stroke(system, [(x1, cap), (x0, 0.0)], thickness=uc)
        + stroke(system, [(x0, 0.0), (x1, 0.0)], thickness=thin)
    )
