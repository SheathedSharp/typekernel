"""Diagonal glyph v — two compensated diagonals meeting at the baseline."""

from __future__ import annotations

import math

from elements import WIDTHS, diagonal_stroke

from typekernel.plugins.passes.diagonal_comp import compensated_weight
from typekernel.project import glyph
from typekernel.system import System


@glyph("v", group="lc.diagonal")
def v(system: System):
    st = float(system.stem["lc"])
    xh = float(system.zones.x)
    width = float(WIDTHS["v"])
    lsb = float(system.tokens.get("lsb_lc", 40.0))
    # Angle of each leg from vertical.
    dx = width / 2.0 - st * 0.15
    dy = xh
    ang = math.degrees(math.atan2(dx, dy))
    w = compensated_weight(st, ang)
    cx = lsb + width / 2.0
    left = diagonal_stroke(
        (lsb + st * 0.35, xh), (cx, 0.0), weight=w, tag_prefix="leg.l"
    )
    right = diagonal_stroke(
        (lsb + width - st * 0.35, xh), (cx, 0.0), weight=w, tag_prefix="leg.r"
    )
    return left + right
