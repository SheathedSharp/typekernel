"""period — baseline pen_dot."""
from __future__ import annotations
from elements import pen_dot
from typekernel.project import glyph
from typekernel.system import System

@glyph("period", group="punct")
def period(system: System):
    r = float(system.tokens["dot_radius"])
    lsb = float(system.tokens.get("lsb_lc", 32.0)) * 0.5
    return pen_dot(system, lsb + r, r * 0.9, radius=r)
