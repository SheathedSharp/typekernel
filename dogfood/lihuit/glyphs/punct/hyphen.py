"""hyphen — anatomy crossbar (P3-7)."""

from __future__ import annotations

from elements import WIDTHS

from typekernel.anatomy import crossbar
from typekernel.project import glyph
from typekernel.system import System


@glyph("hyphen", group="punct")
def hyphen(system: System):
    st = float(system.stem["lc"])
    xh = float(system.zones.x)
    lsb = float(system.tokens.get("lsb_lc", 40.0)) * 0.5
    length = float(WIDTHS.get("hyphen", 220))
    t = st * 0.85
    return crossbar(lsb, lsb + length, xh * 0.48, thick=t, name="bar", ends="none")
