"""Control glyph O — capital slanted oval (shared bowl)."""

from __future__ import annotations

from elements import bowl

from typekernel.project import glyph
from typekernel.system import System


@glyph("O", group="control")
def glyph_O(system: System):
    st = float(system.stem["uc"])
    cap = float(system.zones.cap)
    width = float(system.tokens["O_width"])
    lsb = float(system.tokens.get("lsb_uc", 44.0))
    ov = float(system.overshoot.round)
    cx = lsb + width / 2.0
    cy = cap / 2.0
    rx = width / 2.0 - st * 0.12
    ry = cap / 2.0 + ov - st * 0.12
    return bowl(system, cx=cx, cy=cy, rx=rx, ry=ry, thickness=st)
