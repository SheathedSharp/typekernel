"""Figure 3 — open E with mid bar, gapped joins (G-class)."""

from __future__ import annotations

from elements import stroke

from typekernel.project import glyph
from typekernel.system import System

_GAP = 55.0


@glyph("three", group="figs")
def three(system: System):
    st = float(system.stem["lc"])
    width = float(system.tokens.get("fig_width", 460.0))
    lsb = float(system.tokens.get("lsb_lc", 32.0))
    h = float(system.zones.cap) * 0.72
    gap = _GAP
    x = lsb + width * 0.75
    return (
        stroke(system, [(x, gap), (x, h - gap)], thickness=st)
        + stroke(system, [(lsb + width * 0.2, h), (x - gap, h)], thickness=st)
        + stroke(system, [(lsb + width * 0.25, h * 0.5), (x - gap, h * 0.5)], thickness=st * 0.85)
        + stroke(system, [(lsb + width * 0.2, 0.0), (x - gap, 0.0)], thickness=st)
    )
