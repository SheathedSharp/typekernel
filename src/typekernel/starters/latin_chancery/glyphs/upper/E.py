"""Uppercase E — stem + three bars."""
from __future__ import annotations
from elements import stroke
from typekernel.project import glyph
from typekernel.system import System

@glyph("E", group="uc.straight")
def E(system: System):
    uc = float(system.stem["uc"])
    cap = float(system.zones.cap)
    width = float(system.tokens.get("E_width", 480.0))
    lsb = float(system.tokens.get("lsb_uc", 40.0))
    x0 = lsb + uc * 0.5
    x1 = lsb + width - uc * 0.2
    thin = float(system.stem["uc_h"])
    stem = stroke(system, [(x0, 0.0), (x0, cap)], thickness=uc)
    top = stroke(system, [(x0, cap), (x1, cap)], thickness=thin)
    mid = stroke(system, [(x0, cap * 0.5), (x1 - uc * 0.6, cap * 0.5)], thickness=thin)
    bot = stroke(system, [(x0, 0.0), (x1, 0.0)], thickness=thin)
    return stem + top + mid + bot
