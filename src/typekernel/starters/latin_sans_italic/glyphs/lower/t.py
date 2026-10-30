"""t — short stem + crossbar (interpolation-safe)."""

from __future__ import annotations

from elements import WIDTHS, fuse, stroke

from typekernel.project import glyph
from typekernel.system import System


@glyph("t", group="lc.straight")
def t(system: System):
    st = float(system.stem["lc"])
    xh = float(system.zones.x)
    width = float(WIDTHS.get("t", 280.0))
    lsb = float(system.tokens["lsb_lc"])
    x = lsb + width * 0.45
    top = xh + st * 0.55
    stem = stroke(system, [(x, 0.0), (x, top)], thickness=st)
    bar_y = xh * 0.78
    bar = stroke(system, [(lsb, bar_y), (lsb + width, bar_y)], thickness=st * 0.85)
    return fuse(stem + bar)
