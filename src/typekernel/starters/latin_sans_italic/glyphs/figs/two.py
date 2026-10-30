"""Figure 2 — open E-like with gapped joins (interpolation-safe)."""

from __future__ import annotations

from elements import WIDTHS, stroke

from typekernel.project import glyph
from typekernel.system import System

_GAP = 50.0


@glyph("two", group="figs")
def two(system: System):
    st = float(system.stem["lc"])
    width = float(WIDTHS.get("fig", 460.0))
    lsb = float(system.tokens["lsb_lc"])
    h = float(system.zones.cap) * 0.72
    gap = _GAP
    x = lsb + width * 0.75
    stem = stroke(system, [(x, gap), (x, h - gap)], thickness=st)
    top = stroke(system, [(lsb + width * 0.2, h), (x - gap, h)], thickness=st)
    bot = stroke(system, [(lsb + width * 0.2, 0.0), (x - gap, 0.0)], thickness=st)
    return stem + top + bot
