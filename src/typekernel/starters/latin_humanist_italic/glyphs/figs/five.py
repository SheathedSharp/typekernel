"""Figure 5 — top bar + spine + baseline (interpolation-safe)."""

from __future__ import annotations

from elements import WIDTHS, stroke

from typekernel.project import glyph
from typekernel.system import System

_GAP = 80.0


@glyph("five", group="figs")
def five(system: System):
    st = float(system.stem["lc"])
    width = float(WIDTHS.get("fig", 460.0))
    lsb = float(system.tokens.get("lsb_lc", 36.0))
    h = float(system.zones.cap) * 0.72
    gap = _GAP
    top = stroke(system, [(lsb + width * 0.2, h), (lsb + width * 0.85, h)], thickness=st)
    spine = stroke(
        system, [(lsb + width * 0.28, h - gap), (lsb + width * 0.28, h * 0.5)], thickness=st
    )
    bot = stroke(system, [(lsb + width * 0.2, 0.0), (lsb + width * 0.85, 0.0)], thickness=st)
    return top + spine + bot
