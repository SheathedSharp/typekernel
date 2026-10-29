"""Straight glyph i — anatomy stem + dot (P3-7)."""

from __future__ import annotations

from elements import WIDTHS

from typekernel.anatomy import dot, stem
from typekernel.project import glyph
from typekernel.system import System


@glyph("i", group="lc.straight")
def i(system: System):
    st = float(system.stem["lc"])
    xh = float(system.zones.x)
    width = float(WIDTHS["i"])
    lsb = float(system.tokens.get("lsb_lc", 40.0))
    x0 = lsb + (width - st) / 2.0
    body = stem(x0, x0 + st, 0.0, xh, name="stem")
    diameter = st * 1.1
    cy = xh + float(system.overshoot.round) + diameter * 0.65
    cx = x0 + st / 2.0
    tittle = dot((cx, cy), diameter, shape="round", name="dot")
    return body + tittle
