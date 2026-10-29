"""Straight glyph L — anatomy stem + baseline bar (P3-7)."""

from __future__ import annotations

from elements import WIDTHS, zone_anchors

from typekernel.anatomy import crossbar, stem
from typekernel.project import glyph
from typekernel.system import System


@glyph("L", group="uc.straight")
def glyph_L(system: System):
    uc = float(system.stem["uc"])
    cap = float(system.zones.cap)
    width = float(WIDTHS["L"])
    lsb = float(system.tokens.get("lsb_uc", 50.0))
    bar_t = float(system.tokens.get("bar_thickness", uc * 0.85))
    left = stem(lsb, lsb + uc, 0.0, cap, name="stem.l")
    bar = crossbar(
        lsb + uc * 0.5,
        lsb + width,
        bar_t / 2.0,
        thick=bar_t,
        name="bar",
        ends="none",
    )
    return zone_anchors(left + bar, system, top='cap')
