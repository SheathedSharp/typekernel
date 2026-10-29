"""v — two diagonals meeting at baseline (skeleton+pen)."""

from __future__ import annotations

from elements import fuse, diagonal_stroke

from typekernel.project import glyph
from typekernel.system import System


@glyph("v", group="lc.diag")
def v(system: System):
    st = float(system.stem["lc"])
    xh = float(system.zones.x)
    width = float(system.tokens.get("v_width", 400.0))
    lsb = float(system.tokens.get("lsb_lc", 36.0))
    x0 = lsb + st * 0.3
    x1 = lsb + width - st * 0.3
    mid = (x0 + x1) / 2.0
    left = diagonal_stroke(system, [(x0, xh), (mid, 0.0)], thickness=st)
    right = diagonal_stroke(system, [(x1, xh), (mid, 0.0)], thickness=st)
    return fuse(left + right)
