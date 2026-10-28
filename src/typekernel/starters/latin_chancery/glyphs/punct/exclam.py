"""exclam — stem + pen_dot."""
from __future__ import annotations
from elements import pen_dot, stroke
from typekernel.project import glyph
from typekernel.system import System

@glyph("exclam", group="punct")
def exclam(system: System):
    st = float(system.stem["lc"])
    xh = float(system.zones.x)
    lsb = float(system.tokens.get("lsb_lc", 32.0)) * 0.6
    x = lsb + st * 0.5
    r = float(system.tokens["dot_radius"])
    stem = stroke(system, [(x, r * 3.2), (x, xh)], thickness=st)
    return stem + pen_dot(system, x, r * 0.9, radius=r)
