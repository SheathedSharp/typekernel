"""Diagonal glyph W — four capital diagonals."""

from __future__ import annotations

import math

from elements import WIDTHS, diagonal_stroke

from typekernel.plugins.passes.diagonal_comp import compensated_weight
from typekernel.project import glyph
from typekernel.system import System


@glyph("W", group="uc.diagonal")
def glyph_W(system: System):
    st = float(system.stem["uc"])
    cap = float(system.zones.cap)
    width = float(WIDTHS["W"])
    lsb = float(system.tokens.get("lsb_uc", 50.0))
    t0 = lsb + st * 0.25
    t1 = lsb + width * 0.36
    t2 = lsb + width * 0.64
    t3 = lsb + width - st * 0.25
    b0 = lsb + width * 0.28
    b1 = lsb + width * 0.72
    ang = math.degrees(math.atan2(abs(t1 - b0), cap))
    wt = compensated_weight(st, ang)
    return (
        diagonal_stroke((t0, cap), (b0, 0.0), weight=wt, tag_prefix="W.0")
        + diagonal_stroke((t1, cap), (b0, 0.0), weight=wt, tag_prefix="W.1")
        + diagonal_stroke((t2, cap), (b1, 0.0), weight=wt, tag_prefix="W.2")
        + diagonal_stroke((t3, cap), (b1, 0.0), weight=wt, tag_prefix="W.3")
    )
