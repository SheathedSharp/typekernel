"""o-group glyph b — stem + bowl (overlap)."""

from __future__ import annotations

from elements import bowl, stem_rect

from typekernel.project import glyph
from typekernel.system import System


@glyph("b", group="lc.bowl")
def b(system: System):
    st = float(system.stem["lc"])
    xh = float(system.zones.x)
    asc = float(system.zones.asc)
    ov = float(system.overshoot.round)
    width = float(system.tokens["o_width"])
    lsb = float(system.tokens.get("lsb_lc", 40.0))
    # Stem placement / height depend on letter.
    # Ascender stem on the left, overlapping the bowl.
    stem = stem_rect(lsb, lsb + st, 0.0, asc, prefix="stem.l")

    cx = lsb + width / 2.0
    cy = xh / 2.0
    rx = width / 2.0
    ry = xh / 2.0 + ov
    ring = bowl(system, cx=cx, cy=cy, rx=rx, ry=ry, thickness=st)
    return stem + ring
