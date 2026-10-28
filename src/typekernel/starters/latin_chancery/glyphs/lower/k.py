"""Lowercase k — stem + diagonal arms."""
from __future__ import annotations
from elements import stroke
from typekernel.project import glyph
from typekernel.system import System

@glyph("k", group="lc.diag")
def k(system: System):
    st = float(system.stem["lc"])
    xh = float(system.zones.x)
    asc = float(system.zones.asc)
    width = float(system.tokens.get("k_width", 360.0))
    lsb = float(system.tokens.get("lsb_lc", 32.0))
    x0 = lsb + st * 0.5
    x1 = lsb + width - st * 0.3
    stem = stroke(system, [(x0, 0.0), (x0, asc - 20.0)], thickness=st)
    join_y = xh * 0.42
    upper = stroke(system, [(x0 + st * 0.2, join_y), (x1, xh)], thickness=st)
    lower = stroke(system, [(x0 + st * 0.2, join_y), (x1, 0.0)], thickness=st)
    return stem + upper + lower
