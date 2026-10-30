"""Diagonal glyph w — two overlapping anatomy diagonal_pairs."""

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
    mid = lsb + width / 2.0
    t0 = lsb + st * 0.3
    t3 = lsb + width - st * 0.3
    # Cross the inner top feet so the two ^ shapes share ink (one island).
    t1 = mid + st * 0.35
    t2 = mid - st * 0.35
    b0 = lsb + width * 0.22
    b1 = lsb + width * 0.78
    left = diagonal_pair((b0, 0.0), (t0, xh), (t1, xh), weight=st, name="diag.l")
    right = diagonal_pair((b1, 0.0), (t2, xh), (t3, xh), weight=st, name="diag.r")
    return zone_anchors(left + right, system, top='x')
