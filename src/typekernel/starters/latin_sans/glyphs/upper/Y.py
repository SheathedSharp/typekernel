"""Diagonal glyph Y — upper V + vertical stem."""

from __future__ import annotations

import math

from elements import diagonal_stroke, stem_rect

from typekernel.plugins.passes.diagonal_comp import compensated_weight
from typekernel.project import glyph
from typekernel.system import System


@glyph("Y", group="uc.diagonal")
def glyph_Y(system: System):
    st = float(system.stem["uc"])
    cap = float(system.zones.cap)
    width = float(system.tokens["Y_width"])
    lsb = float(system.tokens.get("lsb_uc", 50.0))
    join_y = cap * 0.45
    cx = lsb + width / 2.0
    dx = width / 2.0 - st * 0.25
    ang = math.degrees(math.atan2(dx, cap - join_y))
    wt = compensated_weight(st, ang)
    left = diagonal_stroke((lsb + st * 0.3, cap), (cx, join_y), weight=wt, tag_prefix="Y.l")
    right = diagonal_stroke(
        (lsb + width - st * 0.3, cap), (cx, join_y), weight=wt, tag_prefix="Y.r"
    )
    stem = stem_rect(cx - st / 2.0, cx + st / 2.0, 0.0, join_y + st * 0.35, prefix="Y.stem")
    return left + right + stem
