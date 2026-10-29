"""endash — anatomy crossbar ."""

from __future__ import annotations

from typekernel.anatomy import crossbar
from typekernel.project import glyph
from typekernel.system import System


@glyph("endash", group="punct")
def endash(system: System):
    st = float(system.stem["lc"])
    xh = float(system.zones.x)
    lsb = float(system.tokens.get("lsb_lc", 40.0)) * 0.4
    length = float(system.tokens.get("n_width", 430)) * 0.55
    t = st * 0.85
    return crossbar(lsb, lsb + length, xh * 0.48, thick=t, name="bar", ends="none")
