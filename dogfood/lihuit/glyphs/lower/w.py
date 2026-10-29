"""Diagonal glyph w — two anatomy diagonal_pairs (P3-7)."""

from __future__ import annotations

from elements import WIDTHS, zone_anchors

from typekernel.anatomy import diagonal_pair
from typekernel.project import glyph
from typekernel.system import System


@glyph("w", group="lc.diagonal")
def w(system: System):
    st = float(system.stem["lc"])
    xh = float(system.zones.x)
    width = float(WIDTHS["w"])
    lsb = float(system.tokens.get("lsb_lc", 40.0))
    t0 = lsb + st * 0.3
    t1 = lsb + width * 0.36
    t2 = lsb + width * 0.64
    t3 = lsb + width - st * 0.3
    b0 = lsb + width * 0.28
    b1 = lsb + width * 0.72
    left = diagonal_pair((b0, 0.0), (t0, xh), (t1, xh), weight=st, name="diag.l")
    right = diagonal_pair((b1, 0.0), (t2, xh), (t3, xh), weight=st, name="diag.r")
    return zone_anchors(left + right, system, top='x')
