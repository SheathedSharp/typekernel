"""Uppercase L — stem + baseline bar."""
from __future__ import annotations
from elements import stroke
from typekernel.project import glyph
from typekernel.system import System

@glyph("L", group="uc.straight")
def L(system: System):
    uc = float(system.stem["uc"])
    cap = float(system.zones.cap)
    width = float(system.tokens.get("L_width", 460.0))
    lsb = float(system.tokens.get("lsb_uc", 40.0))
    x0 = lsb + uc * 0.5
    x1 = lsb + width - uc * 0.2
    stem = stroke(system, [(x0, 0.0), (x0, cap)], thickness=uc)
    bar = stroke(system, [(x0, 0.0), (x1, 0.0)], thickness=float(system.stem["uc_h"]))
    return stem + bar
