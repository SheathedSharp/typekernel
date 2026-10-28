"""quotesingle — short vertical."""
from __future__ import annotations
from elements import stroke
from typekernel.project import glyph
from typekernel.system import System

@glyph("quotesingle", group="punct")
def quotesingle(system: System):
    st = float(system.stem["lc"])
    xh = float(system.zones.x)
    asc = float(system.zones.asc)
    lsb = float(system.tokens.get("lsb_lc", 32.0)) * 0.5
    x = lsb + st * 0.4
    return stroke(system, [(x, xh * 0.85), (x, asc - 20.0)], thickness=st * 0.85)
