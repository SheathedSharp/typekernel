"""Diagonal glyph z — anatomy crossbars + diagonal band (P3-7)."""

from __future__ import annotations

from elements import WIDTHS

from typekernel.anatomy import crossbar
from typekernel.draw import Writer, diagonal_band
from typekernel.project import glyph
from typekernel.system import System


@glyph("z", group="lc.diagonal")
def z(system: System):
    st = float(system.stem["lc"])
    thin = float(system.stem.get("lc_h", st * 0.85))
    xh = float(system.zones.x)
    width = float(WIDTHS["z"])
    lsb = float(system.tokens.get("lsb_lc", 40.0))
    top = crossbar(lsb, lsb + width, xh - thin / 2.0, thick=thin, name="bar.t", ends="none")
    bot = crossbar(lsb, lsb + width, thin / 2.0, thick=thin, name="bar.b", ends="none")
    left, right = diagonal_band(
        (lsb + width - thin * 0.5, xh - thin),
        (lsb + thin * 0.5, thin),
        weight=st,
        compensate=True,
    )
    diag = (
        Writer()
        .start(left.start)
        .corner("diag.top.l")
        .fragment(left)
        .corner("diag.foot.l")
        .line(right.start)
        .corner("diag.foot.r")
        .fragment(right)
        .corner("diag.top.r")
        .line(left.start)
        .close()
        .build()
    )
    return top + bot + diag
