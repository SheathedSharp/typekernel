"""Diagonal glyph V — anatomy diagonal_pair (P3-7)."""

from __future__ import annotations

from elements import WIDTHS, zone_anchors

from typekernel.anatomy import diagonal_pair
from typekernel.project import glyph
from typekernel.system import System


@glyph("V", group="uc.diagonal")
def glyph_V(system: System):
    st = float(system.stem["uc"])
    cap = float(system.zones.cap)
    width = float(WIDTHS["V"])
    lsb = float(system.tokens.get("lsb_uc", 50.0))
    cx = lsb + width / 2.0
    return zone_anchors(
        diagonal_pair(
                (cx, 0.0),
                (lsb + st * 0.3, cap),
                (lsb + width - st * 0.3, cap),
                weight=st,
                name="diag",
            ),
        system,
        top='cap',
    )
