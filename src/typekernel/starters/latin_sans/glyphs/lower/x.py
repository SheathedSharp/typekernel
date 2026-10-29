"""Diagonal glyph x — anatomy crossing (P3-7)."""

from __future__ import annotations

from elements import WIDTHS

from typekernel.anatomy import crossing
from typekernel.project import glyph
from typekernel.system import System


@glyph("x", group="lc.diagonal")
def x(system: System):
    st = float(system.stem["lc"])
    xh = float(system.zones.x)
    width = float(WIDTHS["x"])
    lsb = float(system.tokens.get("lsb_lc", 40.0))
    pad = st * 0.25
    return crossing(
        (lsb + pad, xh),
        (lsb + width - pad, 0.0),
        (lsb + width - pad, xh),
        (lsb + pad, 0.0),
        weight=st,
        name="cross",
    )
