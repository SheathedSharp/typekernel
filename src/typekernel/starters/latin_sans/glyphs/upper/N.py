"""Diagonal glyph N — anatomy stems + diagonal band (P3-7)."""

from __future__ import annotations

from elements import WIDTHS, zone_anchors

from typekernel.anatomy import stem
from typekernel.draw import Writer, diagonal_band
from typekernel.project import glyph
from typekernel.system import System


@glyph("N", group="uc.diagonal")
def glyph_N(system: System):
    st = float(system.stem["uc"])
    cap = float(system.zones.cap)
    width = float(WIDTHS["N"])
    lsb = float(system.tokens.get("lsb_uc", 50.0))
    left = stem(lsb, lsb + st, 0.0, cap, name="stem.l")
    right = stem(lsb + width - st, lsb + width, 0.0, cap, name="stem.r")
    band_l, band_r = diagonal_band(
        (lsb + st * 0.5, cap),
        (lsb + width - st * 0.5, 0.0),
        weight=st,
        compensate=True,
    )
    diag = (
        Writer()
        .start(band_l.start)
        .corner("diag.top.l")
        .fragment(band_l)
        .corner("diag.foot.l")
        .line(band_r.start)
        .corner("diag.foot.r")
        .fragment(band_r)
        .corner("diag.top.r")
        .line(band_l.start)
        .close()
        .build()
    )
    return zone_anchors(left + right + diag, system, top='cap')
