"""Control o — closed oval via cubic bowl + tidy (S1)."""

from __future__ import annotations

from elements import bowl

from typekernel.project import glyph
from typekernel.system import System


@glyph("o", group="control")
def o(system: System):
    st = float(system.stem["lc"])
    xh = float(system.zones.x)
    width = float(system.tokens["o_width"])
    lsb = float(system.tokens["lsb_lc"])
    ov = float(system.overshoot.round)
    cx = lsb + width / 2.0
    cy = xh / 2.0
    rx = width / 2.0 - st * 0.15
    ry = xh / 2.0 + ov * 0.5 - st * 0.15
    return bowl(system, cx=cx, cy=cy, rx=rx, ry=ry, thickness=st)
