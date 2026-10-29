"""Diagonal glyph A — V inverted + crossbar."""

from __future__ import annotations

import math

from elements import WIDTHS, crossbar, diagonal_stroke

from typekernel.plugins.passes.diagonal_comp import compensated_weight
from typekernel.project import glyph
from typekernel.system import System


@glyph("A", group="uc.diagonal")
def glyph_A(system: System):
    st = float(system.stem["uc"])
    cap = float(system.zones.cap)
    width = float(WIDTHS["A"])
    lsb = float(system.tokens.get("lsb_uc", 50.0))
    dx = width / 2.0 - st * 0.2
    ang = math.degrees(math.atan2(dx, cap))
    w = compensated_weight(st, ang)
    cx = lsb + width / 2.0
    left = diagonal_stroke((cx, cap), (lsb + st * 0.25, 0.0), weight=w, tag_prefix="A.l")
    right = diagonal_stroke((cx, cap), (lsb + width - st * 0.25, 0.0), weight=w, tag_prefix="A.r")
    bar = crossbar(
        system,
        x0=lsb + width * 0.22,
        x1=lsb + width * 0.78,
        cy=cap * 0.38,
        tag_prefix="A.bar",
    )
    return left + right + bar
