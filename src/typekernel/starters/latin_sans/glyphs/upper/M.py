"""Diagonal glyph M — anatomy stems + inner diagonal_pair (P3-7)."""

from __future__ import annotations

from elements import WIDTHS

from typekernel.anatomy import diagonal_pair, stem
from typekernel.project import glyph
from typekernel.system import System


@glyph("M", group="uc.diagonal")
def glyph_M(system: System):
    st = float(system.stem["uc"])
    cap = float(system.zones.cap)
    width = float(WIDTHS["M"])
    lsb = float(system.tokens.get("lsb_uc", 50.0))
    left = stem(lsb, lsb + st, 0.0, cap, name="stem.l")
    right = stem(lsb + width - st, lsb + width, 0.0, cap, name="stem.r")
    cx = lsb + width / 2.0
    inner = diagonal_pair(
        (cx, 0.0),
        (lsb + st * 0.5, cap),
        (lsb + width - st * 0.5, cap),
        weight=st,
        name="diag",
    )
    return left + right + inner
