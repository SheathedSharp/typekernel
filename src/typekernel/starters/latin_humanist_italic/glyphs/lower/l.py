"""n-group glyph l — single slanted ascender stem."""

from __future__ import annotations

from elements import stroke

from typekernel.project import glyph
from typekernel.system import System


@glyph("l", group="lc.straight")
def l(system: System):
    st = float(system.stem["lc"])
    asc = float(system.zones.asc)
    lsb = float(system.tokens.get("lsb_lc", 36.0))
    x = lsb + st * 0.5
    return stroke(system, [(x, 0.0), (x, asc)], thickness=st)
