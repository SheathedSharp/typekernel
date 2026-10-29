"""Diagonal glyph V — two capital diagonals."""

from __future__ import annotations

import math

from elements import WIDTHS, diagonal_stroke

from typekernel.plugins.passes.diagonal_comp import compensated_weight
from typekernel.project import glyph
from typekernel.system import System


@glyph("V", group="uc.diagonal")
def glyph_V(system: System):
    st = float(system.stem["uc"])
    cap = float(system.zones.cap)
    width = float(WIDTHS["V"])
    lsb = float(system.tokens.get("lsb_uc", 50.0))
    dx = width / 2.0 - st * 0.2
    ang = math.degrees(math.atan2(dx, cap))
    w = compensated_weight(st, ang)
    cx = lsb + width / 2.0
    return diagonal_stroke((lsb + st * 0.3, cap), (cx, 0.0), weight=w, tag_prefix="V.l") +         diagonal_stroke((lsb + width - st * 0.3, cap), (cx, 0.0), weight=w, tag_prefix="V.r")
