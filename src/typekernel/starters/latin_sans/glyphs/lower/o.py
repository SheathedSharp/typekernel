"""Control glyph o — bowl / counter with round overshoot."""

from __future__ import annotations

from elements import bowl

from typekernel.project import glyph
from typekernel.system import System


@glyph("o", group="lc.bowl")
def o(system: System):
    width = float(system.tokens["o_width"])
    lsb = float(system.tokens.get("lsb_lc", 40.0))
    xh = float(system.zones.x)
    ov = float(system.overshoot.round)
    st = float(system.stem["lc"])
    cx = lsb + width / 2.0
    cy = xh / 2.0
    rx = width / 2.0
    ry = xh / 2.0 + ov
    return bowl(system, cx=cx, cy=cy, rx=rx, ry=ry, thickness=st)
