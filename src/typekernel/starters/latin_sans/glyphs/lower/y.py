"""Diagonal glyph y — v-like top + descender diagonal."""

from __future__ import annotations

import math

from elements import diagonal_stroke

from typekernel.plugins.passes.diagonal_comp import compensated_weight
from typekernel.project import glyph
from typekernel.system import System


@glyph("y", group="lc.diagonal")
def y(system: System):
    st = float(system.stem["lc"])
    xh = float(system.zones.x)
    desc = float(system.zones.desc)
    width = float(system.tokens["y_width"])
    lsb = float(system.tokens.get("lsb_lc", 40.0))
    cx = lsb + width / 2.0
    # Join slightly above baseline so the descender continues the right leg.
    join_y = xh * 0.38
    dx = width / 2.0 - st * 0.2
    ang = math.degrees(math.atan2(dx, xh - join_y))
    wt = compensated_weight(st, ang)
    left = diagonal_stroke(
        (lsb + st * 0.35, xh), (cx, join_y), weight=wt, tag_prefix="y.l"
    )
    right = diagonal_stroke(
        (lsb + width - st * 0.35, xh), (cx, join_y), weight=wt, tag_prefix="y.r"
    )
    # Descender continues from join toward bottom-leftish (classic italic-ish y
    # would go left; geometric sans often continues the right diagonal down).
    ang_d = math.degrees(math.atan2(dx * 0.55, join_y - desc))
    wt_d = compensated_weight(st, ang_d)
    descender = diagonal_stroke(
        (cx, join_y),
        (lsb + width * 0.22, desc),
        weight=wt_d,
        tag_prefix="y.desc",
    )
    return left + right + descender
