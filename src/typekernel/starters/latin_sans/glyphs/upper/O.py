"""Control glyph O — capital bowl / counter with round overshoot."""

from __future__ import annotations

from elements import bowl

from typekernel.project import glyph
from typekernel.system import System


@glyph("O", group="uc.bowl")
def O(system: System):
    width = float(system.tokens["O_width"])
    lsb = float(system.tokens.get("lsb_uc", 50.0))
    cap = float(system.zones.cap)
    ov = float(system.overshoot.round)
    st = float(system.stem["uc"])
    cx = lsb + width / 2.0
    cy = cap / 2.0
    rx = width / 2.0
    ry = cap / 2.0 + ov
    return bowl(system, cx=cx, cy=cy, rx=rx, ry=ry, thickness=st)
