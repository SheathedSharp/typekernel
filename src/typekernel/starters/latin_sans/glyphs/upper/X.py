"""Diagonal glyph X — anatomy crossing (P3-7)."""

from __future__ import annotations

from elements import WIDTHS, zone_anchors

from typekernel.anatomy import crossing
from typekernel.project import glyph
from typekernel.system import System


@glyph("X", group="uc.diagonal")
def glyph_X(system: System):
    st = float(system.stem["uc"])
    cap = float(system.zones.cap)
    width = float(WIDTHS["X"])
    lsb = float(system.tokens.get("lsb_uc", 50.0))
    pad = st * 0.2
    return zone_anchors(
        crossing(
                (lsb + pad, cap),
                (lsb + width - pad, 0.0),
                (lsb + width - pad, cap),
                (lsb + pad, 0.0),
                weight=st,
                name="cross",
            ),
        system,
        top='cap',
    )
