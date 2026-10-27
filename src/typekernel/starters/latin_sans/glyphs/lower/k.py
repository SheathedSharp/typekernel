"""Diagonal glyph k — vertical stem + upper/lower arm diagonals."""

from __future__ import annotations

import math

from elements import diagonal_stroke, stem_rect

from typekernel.plugins.passes.diagonal_comp import compensated_weight
from typekernel.project import glyph
from typekernel.system import System


@glyph("k", group="lc.diagonal")
def k(system: System):
    st = float(system.stem["lc"])
    xh = float(system.zones.x)
    width = float(system.tokens["k_width"])
    lsb = float(system.tokens.get("lsb_lc", 40.0))
    stem = stem_rect(lsb, lsb + st, 0.0, xh, prefix="stem.l")
    # Arms meet the stem around mid x-height.
    join_y = xh * 0.48
    join_x = lsb + st * 0.65
    dx = width - st
    ang_u = math.degrees(math.atan2(dx, xh - join_y))
    ang_l = math.degrees(math.atan2(dx, join_y))
    wu = compensated_weight(st, ang_u)
    wl = compensated_weight(st, ang_l)
    upper = diagonal_stroke(
        (lsb + width - st * 0.25, xh),
        (join_x, join_y),
        weight=wu,
        tag_prefix="k.upper",
    )
    lower = diagonal_stroke(
        (join_x, join_y),
        (lsb + width - st * 0.25, 0.0),
        weight=wl,
        tag_prefix="k.lower",
    )
    return stem + upper + lower
