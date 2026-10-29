"""quotedbl — two anatomy stem quotes (P3-7)."""

from __future__ import annotations

from typekernel.anatomy import stem
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
    left = stem(lsb, lsb + w, cap - h, cap, name="stem.l")
    right = stem(lsb + w + gap, lsb + w + gap + w, cap - h, cap, name="stem.r")
    return left + right
