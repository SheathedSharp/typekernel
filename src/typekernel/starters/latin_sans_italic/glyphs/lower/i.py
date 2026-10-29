"""Control i — stem + tittle."""

from __future__ import annotations

from elements import stroke

from typekernel.anatomy.pen import pen_dot
from typekernel.project import glyph
from typekernel.system import System


@glyph("i", group="control")
def i(system: System):
    st = float(system.stem["lc"])
    xh = float(system.zones.x)
    lsb = float(system.tokens["lsb_lc"])
    x = lsb + st * 0.5
    stem = stroke(system, [(x, 0.0), (x, xh)], thickness=st)
    dot = pen_dot(system, x, xh + st * 1.15)
    return stem + dot
