"""Uppercase I — single stem with serifs as short bars."""
from __future__ import annotations
from elements import stroke
from typekernel.project import glyph
from typekernel.system import System

@glyph("I", group="uc.straight")
def I(system: System):
    uc = float(system.stem["uc"])
    cap = float(system.zones.cap)
    lsb = float(system.tokens.get("lsb_uc", 40.0))
    x = lsb + uc * 0.5
    thin = float(system.stem["uc_h"])
    stem = stroke(system, [(x, 0.0), (x, cap)], thickness=uc)
    top = stroke(system, [(x - uc * 0.9, cap), (x + uc * 0.9, cap)], thickness=thin)
    bot = stroke(system, [(x - uc * 0.9, 0.0), (x + uc * 0.9, 0.0)], thickness=thin)
    return stem + top + bot
