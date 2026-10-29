"""Diagonal glyph W — two anatomy diagonal_pairs ."""

from __future__ import annotations

from elements import WIDTHS, zone_anchors

from typekernel.anatomy import diagonal_pair
from typekernel.project import glyph
from typekernel.system import System


@glyph("W", group="uc.diagonal")
def glyph_W(system: System):
    st = float(system.stem["uc"])
    cap = float(system.zones.cap)
    width = float(WIDTHS["W"])
    lsb = float(system.tokens.get("lsb_uc", 50.0))
    t0 = lsb + st * 0.25
    t1 = lsb + width * 0.36
    t2 = lsb + width * 0.64
    t3 = lsb + width - st * 0.25
    b0 = lsb + width * 0.28
    b1 = lsb + width * 0.72
    left = diagonal_pair((b0, 0.0), (t0, cap), (t1, cap), weight=st, name="diag.l")
    right = diagonal_pair((b1, 0.0), (t2, cap), (t3, cap), weight=st, name="diag.r")
    return zone_anchors(left + right, system, top='cap')
