"""Diagonal glyph X — crossing capitals."""

from __future__ import annotations

import math

from elements import WIDTHS, diagonal_stroke

from typekernel.plugins.passes.diagonal_comp import compensated_weight
from typekernel.project import glyph
from typekernel.system import System


@glyph("X", group="uc.diagonal")
def glyph_X(system: System):
    st = float(system.stem["uc"])
    cap = float(system.zones.cap)
    width = float(WIDTHS["X"])
    lsb = float(system.tokens.get("lsb_uc", 50.0))
    pad = st * 0.2
    ang = math.degrees(math.atan2(width - 2 * pad, cap))
    wt = compensated_weight(st, ang)
    return diagonal_stroke(
        (lsb + pad, cap), (lsb + width - pad, 0.0), weight=wt, tag_prefix="X.nw"
    ) + diagonal_stroke(
        (lsb + width - pad, cap), (lsb + pad, 0.0), weight=wt, tag_prefix="X.ne"
    )
