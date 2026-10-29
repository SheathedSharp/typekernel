"""Round glyph a — bowl + right stem (double-storey geometric sans)."""

from __future__ import annotations

from elements import WIDTHS, bowl, stem_rect

from typekernel.project import glyph
from typekernel.system import System


@glyph("a", group="lc.round")
def a(system: System):
    st = float(system.stem["lc"])
    xh = float(system.zones.x)
    width = float(WIDTHS["a"])
    lsb = float(system.tokens.get("lsb_lc", 40.0))
    ov = float(system.overshoot.round)
    # Right stem full x-height; bowl sits to the left overlapping it.
    stem = stem_rect(lsb + width - st, lsb + width, 0.0, xh, prefix="stem.r")
    # Bowl centered in the left portion, slightly below x-height.
    bowl_w = width - st * 0.55
    cx = lsb + bowl_w / 2.0
    cy = xh * 0.48
    rx = bowl_w / 2.0
    ry = xh * 0.48 + ov * 0.5
    ring = bowl(system, cx=cx, cy=cy, rx=rx, ry=ry, thickness=st)
    return stem + ring
