"""Diagonal glyph z — top/bottom bars + compensated diagonal."""

from __future__ import annotations

import math

from elements import WIDTHS, diagonal_stroke, stem_rect

from typekernel.plugins.passes.diagonal_comp import compensated_weight
from typekernel.project import glyph
from typekernel.system import System


@glyph("z", group="lc.diagonal")
def z(system: System):
    st = float(system.stem["lc"])
    xh = float(system.zones.x)
    width = float(WIDTHS["z"])
    lsb = float(system.tokens.get("lsb_lc", 40.0))
    bar = float(system.stem.get("lc_h", st * 0.85))
    top = stem_rect(lsb, lsb + width, xh - bar, xh, prefix="z.top")
    bot = stem_rect(lsb, lsb + width, 0.0, bar, prefix="z.bot")
    # Diagonal from top-right inner to bottom-left inner.
    dx = width - st
    dy = xh - 2 * bar
    ang = math.degrees(math.atan2(dx, dy))
    wt = compensated_weight(st, ang)
    diag = diagonal_stroke(
        (lsb + width - bar * 0.5, xh - bar),
        (lsb + bar * 0.5, bar),
        weight=wt,
        tag_prefix="z.diag",
    )
    return top + bot + diag
