"""Diagonal glyph y — anatomy diagonal_pair + descender band ."""

from __future__ import annotations

from elements import WIDTHS, zone_anchors

from typekernel.anatomy import diagonal_pair
from typekernel.draw import Writer, diagonal_band
from typekernel.project import glyph
from typekernel.system import System


@glyph("y", group="lc.diagonal")
def y(system: System):
    st = float(system.stem["lc"])
    xh = float(system.zones.x)
    desc = float(system.zones.desc)
    width = float(WIDTHS["y"])
    lsb = float(system.tokens.get("lsb_lc", 40.0))
    cx = lsb + width / 2.0
    join_y = xh * 0.38
    top = diagonal_pair(
        (cx, join_y),
        (lsb + st * 0.35, xh),
        (lsb + width - st * 0.35, xh),
        weight=st,
        name="diag",
    )
    left, right = diagonal_band(
        (cx, join_y), (lsb + width * 0.22, desc), weight=st, compensate=True
    )
    descender = (
        Writer()
        .start(left.start)
        .corner("tail.top.l")
        .fragment(left)
        .corner("tail.foot.l")
        .line(right.start)
        .corner("tail.foot.r")
        .fragment(right)
        .corner("tail.top.r")
        .line(left.start)
        .close()
        .build()
    )
    return zone_anchors(top + descender, system, top='x')
