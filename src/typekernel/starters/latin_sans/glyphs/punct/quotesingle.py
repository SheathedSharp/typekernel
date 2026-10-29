"""quotesingle — anatomy stem quote ."""

from __future__ import annotations

from typekernel.anatomy import stem
from typekernel.project import glyph
from typekernel.system import System


@glyph("quotesingle", group="punct")
def quotesingle(system: System):
    st = float(system.stem["lc"])
    cap = float(system.zones.cap)
    lsb = float(system.tokens.get("lsb_lc", 40.0)) * 0.45
    h = st * 2.2
    return stem(lsb, lsb + st * 0.75, cap - h, cap, name="stem")
