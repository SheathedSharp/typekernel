"""quotedbl — two vertical quote marks."""

from __future__ import annotations

from elements import stem_rect

from typekernel.project import glyph
from typekernel.system import System


@glyph("quotedbl", group="punct")
def quotedbl(system: System):
    st = float(system.stem["lc"])
    cap = float(system.zones.cap)
    lsb = float(system.tokens.get("lsb_lc", 40.0)) * 0.4
    h = st * 2.2
    w = st * 0.7
    gap = st * 0.55
    left = stem_rect(lsb, lsb + w, cap - h, cap, prefix="quote.l")
    right = stem_rect(lsb + w + gap, lsb + w + gap + w, cap - h, cap, prefix="quote.r")
    return left + right
