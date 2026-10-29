"""Straight glyph E — anatomy stem + three bars (P3-7)."""

from __future__ import annotations

from elements import WIDTHS

from typekernel.anatomy import crossbar, stem
from typekernel.project import glyph
from typekernel.system import System


@glyph("E", group="uc.straight")
def glyph_E(system: System):
    uc = float(system.stem["uc"])
    cap = float(system.zones.cap)
    width = float(WIDTHS["E"])
    lsb = float(system.tokens.get("lsb_uc", 50.0))
    bar_t = float(system.tokens.get("bar_thickness", uc * 0.85))
    left = stem(lsb, lsb + uc, 0.0, cap, name="stem.l")
    top = crossbar(
        lsb + uc * 0.5,
        lsb + width,
        cap - bar_t / 2.0,
        thick=bar_t,
        name="bar.t",
        ends="none",
    )
    mid = crossbar(
        lsb + uc * 0.5,
        lsb + width * 0.82,
        cap * 0.5,
        thick=bar_t,
        name="bar.1",
        ends="none",
    )
    bot = crossbar(
        lsb + uc * 0.5,
        lsb + width,
        bar_t / 2.0,
        thick=bar_t,
        name="bar.b",
        ends="none",
    )
    return left + top + mid + bot
