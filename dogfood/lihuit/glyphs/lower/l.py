"""Straight glyph l — tall anatomy stem (P3-7)."""

from __future__ import annotations

from elements import WIDTHS, zone_anchors

from typekernel.anatomy import stem
from typekernel.project import glyph
from typekernel.system import System


@glyph("l", group="lc.straight")
def glyph_l(system: System):
    st = float(system.stem["lc"])
    asc = float(system.zones.asc)
    width = float(WIDTHS["l"])
    lsb = float(system.tokens.get("lsb_lc", 40.0))
    x0 = lsb + (width - st) / 2.0
    return zone_anchors(stem(x0, x0 + st, 0.0, asc, name="stem"), system, top='x')
