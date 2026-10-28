"""Lowercase x — crossing diagonals."""
from __future__ import annotations

from elements import stroke

from typekernel.project import glyph
from typekernel.system import System


@glyph("x", group="lc.diag")
def x(system: System):
    st = float(system.stem["lc"])
    xh = float(system.zones.x)
    width = float(system.tokens.get("x_width", 360.0))
    lsb = float(system.tokens.get("lsb_lc", 32.0))
    x0 = lsb + st * 0.2
    x1 = lsb + width - st * 0.2
    return stroke(system, [(x0, 0.0), (x1, xh)], thickness=st) + stroke(
        system, [(x0, xh), (x1, 0.0)], thickness=st
    )
