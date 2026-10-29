"""n-group glyph l — ascender stem."""

from __future__ import annotations

from elements import stroke

from typekernel.project import glyph
from typekernel.system import System


@glyph("l", group="lc.straight")
def l(system: System):
    st = float(system.stem["lc"])
    asc = float(system.zones.asc)
    width = float(system.tokens.get("l_width", 220.0))
    lsb = float(system.tokens["lsb_lc"])
    x = lsb + width / 2.0
    return stroke(system, [(x, 0.0), (x, asc)], thickness=st)
