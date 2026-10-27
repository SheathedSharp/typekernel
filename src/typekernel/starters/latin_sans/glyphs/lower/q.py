"""o-group glyph q — stem + bowl (overlap)."""

from __future__ import annotations

from elements import bowl, stem_rect

from typekernel.project import glyph
from typekernel.system import System


@glyph("q", group="lc.bowl")
def q(system: System):
    st = float(system.stem["lc"])
    xh = float(system.zones.x)
    desc = float(system.zones.desc)
    ov = float(system.overshoot.round)
    width = float(system.tokens["o_width"])
    lsb = float(system.tokens.get("lsb_lc", 40.0))
    # Stem placement / height depend on letter.
    # Descender stem on the right.
    stem = stem_rect(lsb + width - st, lsb + width, desc, xh, prefix="stem.r")

    cx = lsb + width / 2.0
    cy = xh / 2.0
    rx = width / 2.0
    ry = xh / 2.0 + ov
    ring = bowl(system, cx=cx, cy=cy, rx=rx, ry=ry, thickness=st)
    return stem + ring
