"""n-group glyph m — two arched n-units with mid gap."""

from __future__ import annotations

from elements import stroke

from typekernel.project import glyph
from typekernel.system import System


@glyph("m", group="lc.straight")
def m(system: System):
    st = float(system.stem["lc"])
    xh = float(system.zones.x)
    width = float(system.tokens.get("m_width", 680.0))
    lsb = float(system.tokens["lsb_lc"])
    x0 = lsb + st * 0.5
    x2 = lsb + width - st * 0.5
    x1 = (x0 + x2) / 2.0
    sep = 50.0

    def unit(xa: float, xb: float):
        left = stroke(system, [(xa, 0.0), (xa, xh)], thickness=st)
        right = stroke(system, [(xb, 0.0), (xb, xh * 0.55)], thickness=st)
        arch = stroke(
            system,
            [
                (xa, xh * 0.55),
                (xa, xh),
                ((xa + xb) / 2.0, xh + st * 0.15),
                (xb, xh),
                (xb, xh * 0.55),
            ],
            thickness=st,
        )
        return left + arch + right

    return unit(x0, x1 - sep) + unit(x1 + sep, x2)
