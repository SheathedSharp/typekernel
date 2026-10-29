"""Rest glyph M — outer stems + inner diagonals."""

from __future__ import annotations

import math

from elements import WIDTHS, diagonal_stroke, stem_rect

from typekernel.plugins.passes.diagonal_comp import compensated_weight
from typekernel.project import glyph
from typekernel.system import System


@glyph("M", group="uc.diagonal")
def glyph_M(system: System):
    st = float(system.stem["uc"])
    cap = float(system.zones.cap)
    width = float(WIDTHS["M"])
    lsb = float(system.tokens.get("lsb_uc", 50.0))
    left = stem_rect(lsb, lsb + st, 0.0, cap, prefix="stem.l")
    right = stem_rect(lsb + width - st, lsb + width, 0.0, cap, prefix="stem.r")
    cx = lsb + width / 2.0
    ang = math.degrees(math.atan2(width * 0.35, cap))
    wt = compensated_weight(st, ang)
    d1 = diagonal_stroke((lsb + st * 0.5, cap), (cx, 0.0), weight=wt, tag_prefix="M.l")
    d2 = diagonal_stroke((lsb + width - st * 0.5, cap), (cx, 0.0), weight=wt, tag_prefix="M.r")
    return left + right + d1 + d2
