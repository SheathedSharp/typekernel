"""O-group glyph D — stem + bowl on the right."""

from __future__ import annotations

from elements import bowl, stem_rect

from typekernel.project import glyph
from typekernel.system import System


@glyph("D", group="uc.bowl")
def glyph_D(system: System):
    st = float(system.stem["uc"])
    cap = float(system.zones.cap)
    width = float(system.tokens["D_width"])
    lsb = float(system.tokens.get("lsb_uc", 50.0))
    ov = float(system.overshoot.round)
    stem = stem_rect(lsb, lsb + st, 0.0, cap, prefix="stem.l")
    # Bowl centered to the right of the stem, overlapping it.
    cx = lsb + st + (width - st) / 2.0
    cy = cap / 2.0
    rx = (width - st) / 2.0 + st * 0.35
    ry = cap / 2.0 + ov
    ring = bowl(system, cx=cx, cy=cy, rx=rx, ry=ry, thickness=st)
    return stem + ring
