"""Control glyph H — two slanted stems + bar."""
from __future__ import annotations
from elements import stroke
from typekernel.project import glyph
from typekernel.system import System

@glyph("H", group="control")
def H(system: System):
    st = float(system.stem["uc"])
    cap = float(system.zones.cap)
    width = float(system.tokens["H_width"])
    lsb = float(system.tokens.get("lsb_uc", 40.0))
    x0 = lsb + st * 0.5
    x1 = lsb + width - st * 0.5
    left = stroke(system, [(x0, 0.0), (x0, cap)], thickness=st)
    right = stroke(system, [(x1, 0.0), (x1, cap)], thickness=st)
    bar_y = cap * 0.48
    bar = stroke(system, [(x0, bar_y), (x1, bar_y)], thickness=float(system.stem["uc_h"]))
    return left + right + bar
