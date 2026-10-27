"""quotesingle — vertical quote mark."""

from __future__ import annotations

from elements import stem_rect

from typekernel.project import glyph
from typekernel.system import System


@glyph("quotesingle", group="punct")
def quotesingle(system: System):
    st = float(system.stem["lc"])
    cap = float(system.zones.cap)
    lsb = float(system.tokens.get("lsb_lc", 40.0)) * 0.45
    h = st * 2.2
    return stem_rect(lsb, lsb + st * 0.75, cap - h, cap, prefix="quote")
