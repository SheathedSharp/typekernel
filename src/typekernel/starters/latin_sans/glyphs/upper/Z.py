"""Diagonal glyph Z — anatomy bars + diagonal band (P3-7)."""

from __future__ import annotations

from elements import WIDTHS

from typekernel.anatomy import crossbar
from typekernel.draw import Writer, diagonal_band
from typekernel.project import glyph
from typekernel.system import System


@glyph("Z", group="uc.diagonal")
def glyph_Z(system: System):
    st = float(system.stem["uc"])
    thin = float(system.stem.get("uc_h", st * 0.85))
    cap = float(system.zones.cap)
    width = float(WIDTHS["Z"])
    lsb = float(system.tokens.get("lsb_uc", 50.0))
    top = crossbar(lsb, lsb + width, cap - thin / 2.0, thick=thin, name="bar.t", ends="none")
    bot = crossbar(lsb, lsb + width, thin / 2.0, thick=thin, name="bar.b", ends="none")
    left, right = diagonal_band(
        (lsb + width - thin * 0.4, cap - thin),
        (lsb + thin * 0.4, thin),
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
