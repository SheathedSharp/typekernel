"""x — crossing diagonals (skeleton+pen)."""

from __future__ import annotations

from elements import stroke

from typekernel.project import glyph
from typekernel.system import System


@glyph("x", group="lc.diag")
def x(system: System):
    st = float(system.stem["lc"])
    xh = float(system.zones.x)
    width = float(system.tokens.get("x_width", 400.0))
    lsb = float(system.tokens.get("lsb_lc", 36.0))
    x0 = lsb + st * 0.25
    x1 = lsb + width - st * 0.25
    a = stroke(system, [(x0, xh), (x1, 0.0)], thickness=st)
    b = stroke(system, [(x1, xh), (x0, 0.0)], thickness=st)
    return a + b
