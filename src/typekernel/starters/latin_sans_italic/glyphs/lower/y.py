"""y — v-join with descender."""

from __future__ import annotations

from elements import fuse, stroke

from typekernel.project import glyph
from typekernel.system import System


@glyph("y", group="lc.diag")
def y(system: System):
    st = float(system.stem["lc"])
    xh = float(system.zones.x)
    desc = float(system.zones.desc)
    width = float(system.tokens.get("y_width", 420.0))
    lsb = float(system.tokens["lsb_lc"])
    x0 = lsb + st * 0.3
    x1 = lsb + width - st * 0.3
    mid = (x0 + x1) / 2.0
    return fuse(
        stroke(system, [(x0, xh), (mid, xh * 0.15)], thickness=st)
        + stroke(system, [(x1, xh), (mid, xh * 0.15), (mid - st * 0.4, desc)], thickness=st)
    )
