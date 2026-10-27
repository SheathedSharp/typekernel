"""Diagonal glyph K — stem + arms."""

from __future__ import annotations

import math

from elements import diagonal_stroke, stem_rect

from typekernel.plugins.passes.diagonal_comp import compensated_weight
from typekernel.project import glyph
from typekernel.system import System


@glyph("K", group="uc.diagonal")
def glyph_K(system: System):
    st = float(system.stem["uc"])
    cap = float(system.zones.cap)
    width = float(system.tokens["K_width"])
    lsb = float(system.tokens.get("lsb_uc", 50.0))
    stem = stem_rect(lsb, lsb + st, 0.0, cap, prefix="stem.l")
    join_y = cap * 0.48
    join_x = lsb + st * 0.7
    dx = width - st
    wu = compensated_weight(st, math.degrees(math.atan2(dx, cap - join_y)))
    wl = compensated_weight(st, math.degrees(math.atan2(dx, join_y)))
    upper = diagonal_stroke(
        (lsb + width - st * 0.2, cap), (join_x, join_y), weight=wu, tag_prefix="K.u"
    )
    lower = diagonal_stroke(
        (join_x, join_y), (lsb + width - st * 0.2, 0.0), weight=wl, tag_prefix="K.l"
    )
    return stem + upper + lower
