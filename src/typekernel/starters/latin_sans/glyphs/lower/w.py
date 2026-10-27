"""Diagonal glyph w — four diagonals (two V shapes)."""

from __future__ import annotations

import math

from elements import diagonal_stroke

from typekernel.plugins.passes.diagonal_comp import compensated_weight
from typekernel.project import glyph
from typekernel.system import System


@glyph("w", group="lc.diagonal")
def w(system: System):
    st = float(system.stem["lc"])
    xh = float(system.zones.x)
    width = float(system.tokens["w_width"])
    lsb = float(system.tokens.get("lsb_lc", 40.0))
    # Four top points, two bottom apexes, one mid peak.
    t0 = lsb + st * 0.3
    t1 = lsb + width * 0.36
    t2 = lsb + width * 0.64
    t3 = lsb + width - st * 0.3
    b0 = lsb + width * 0.28
    b1 = lsb + width * 0.72
    dx = abs(t1 - b0)
    ang = math.degrees(math.atan2(dx, xh))
    wt = compensated_weight(st, ang)
    return (
        diagonal_stroke((t0, xh), (b0, 0.0), weight=wt, tag_prefix="w.0")
        + diagonal_stroke((t1, xh), (b0, 0.0), weight=wt, tag_prefix="w.1")
        + diagonal_stroke((t2, xh), (b1, 0.0), weight=wt, tag_prefix="w.2")
        + diagonal_stroke((t3, xh), (b1, 0.0), weight=wt, tag_prefix="w.3")
        # mid peak joins the two inner tops — small overlap bridge optional;
        # the two inner diagonals already meet near mid at x-height.
    )
