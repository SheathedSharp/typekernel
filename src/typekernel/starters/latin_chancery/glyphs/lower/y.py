"""y — shallow cup + mid descender (G-class)."""

from __future__ import annotations

from elements import fuse, stroke

from typekernel.project import glyph
from typekernel.system import System


@glyph("y", group="lc.diag")
def y(system: System):
    st = float(system.stem["lc"])
    xh = float(system.zones.x)
    desc = float(system.zones.desc)
    width = float(system.tokens.get("y_width", 400.0))
    lsb = float(system.tokens.get("lsb_lc", 32.0))
    x0 = lsb + st * 0.35
    x1 = lsb + width - st * 0.35
    mid = lsb + width / 2.0
    cup_y = xh * 0.35
    return fuse(
        stroke(system, [(x0, xh), (x0, cup_y), (x1, cup_y), (x1, xh)], thickness=st)
        + stroke(system, [(mid, cup_y), (mid, desc)], thickness=st)
    )
