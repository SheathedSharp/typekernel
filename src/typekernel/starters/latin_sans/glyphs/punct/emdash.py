"""emdash — anatomy crossbar (P3-7)."""

from __future__ import annotations

from typekernel.anatomy import crossbar
from typekernel.project import glyph
from typekernel.system import System


@glyph("emdash", group="punct")
def emdash(system: System):
    st = float(system.stem["lc"])
    xh = float(system.zones.x)
    lsb = float(system.tokens.get("lsb_lc", 40.0)) * 0.3
    length = float(system.upm) * 0.9
    t = st * 0.85
    return crossbar(lsb, lsb + length, xh * 0.48, thick=t, name="bar", ends="none")
