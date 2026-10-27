"""Diagonal glyph x — crossing pair of compensated diagonals."""

from __future__ import annotations

import math

from elements import diagonal_stroke

from typekernel.plugins.passes.diagonal_comp import compensated_weight
from typekernel.project import glyph
from typekernel.system import System


@glyph("x", group="lc.diagonal")
def x(system: System):
    st = float(system.stem["lc"])
    xh = float(system.zones.x)
    width = float(system.tokens["x_width"])
    lsb = float(system.tokens.get("lsb_lc", 40.0))
    pad = st * 0.25
    dx = width - 2 * pad
    ang = math.degrees(math.atan2(dx, xh))
    wt = compensated_weight(st, ang)
    a = diagonal_stroke(
        (lsb + pad, xh), (lsb + width - pad, 0.0), weight=wt, tag_prefix="x.nw"
    )
    b = diagonal_stroke(
        (lsb + width - pad, xh), (lsb + pad, 0.0), weight=wt, tag_prefix="x.ne"
    )
    return a + b
