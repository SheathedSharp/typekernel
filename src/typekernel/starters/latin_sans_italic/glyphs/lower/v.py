"""v — two diagonals meeting at baseline."""

from __future__ import annotations

from elements import WIDTHS, fuse, stroke

from typekernel.project import glyph
from typekernel.system import System


@glyph("v", group="lc.diag")
def v(system: System):
    st = float(system.stem["lc"])
    xh = float(system.zones.x)
    width = float(WIDTHS.get("v", 420.0))
    lsb = float(system.tokens["lsb_lc"])
    x0 = lsb + st * 0.3
    x1 = lsb + width - st * 0.3
    mid = (x0 + x1) / 2.0
    return fuse(
        stroke(system, [(x0, xh), (mid, 0.0)], thickness=st)
        + stroke(system, [(x1, xh), (mid, 0.0)], thickness=st)
    )
