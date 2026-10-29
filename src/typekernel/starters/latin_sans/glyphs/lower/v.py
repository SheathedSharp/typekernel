"""Diagonal glyph v — anatomy diagonal_pair (P3-7)."""

from __future__ import annotations

from elements import WIDTHS

from typekernel.anatomy import diagonal_pair
from typekernel.project import glyph
from typekernel.system import System


@glyph("v", group="lc.diagonal")
def v(system: System):
    st = float(system.stem["lc"])
    xh = float(system.zones.x)
    width = float(WIDTHS["v"])
    lsb = float(system.tokens.get("lsb_lc", 40.0))
    cx = lsb + width / 2.0
    return diagonal_pair(
        (cx, 0.0),
        (lsb + st * 0.35, xh),
        (lsb + width - st * 0.35, xh),
        weight=st,
        name="diag",
    )
