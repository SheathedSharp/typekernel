"""Diagonal glyph v — anatomy diagonal_pair ."""

from __future__ import annotations

from elements import WIDTHS, zone_anchors

from typekernel.anatomy import diagonal_pair
from typekernel.project import glyph
from typekernel.system import System


@glyph("v", group="lc.diagonal")
def v(system: System):
    st = float(system.stem["lc"])
    xh = float(system.zones.x)
    width = float(WIDTHS["v"])
    lsb = float(system.tokens.get("lsb_lc", 40.0))
    cx = lsb + width / 2.0
    return zone_anchors(
        diagonal_pair(
                (cx, 0.0),
                (lsb + st * 0.35, xh),
                (lsb + width - st * 0.35, xh),
                weight=st,
                name="diag",
            ),
        system,
        top='x',
    )
