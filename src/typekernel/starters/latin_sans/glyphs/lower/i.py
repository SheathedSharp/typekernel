"""Straight glyph i — stem + tittle."""

from __future__ import annotations

from elements import WIDTHS, stem_rect

from typekernel.project import glyph
from typekernel.system import System


@glyph("i", group="lc.straight")
def i(system: System):
    st = float(system.stem["lc"])
    xh = float(system.zones.x)
    width = float(WIDTHS["i"])
    lsb = float(system.tokens.get("lsb_lc", 40.0))
    x0 = lsb + (width - st) / 2.0
    stem = stem_rect(x0, x0 + st, 0.0, xh, prefix="stem")
    dot_r = st * 0.55
    cy = xh + float(system.overshoot.round) + dot_r * 1.15
    cx = x0 + st / 2.0
    tittle = stem_rect(cx - dot_r, cx + dot_r, cy - dot_r, cy + dot_r, prefix="tittle")
    return stem + tittle
