"""Lowercase w — double v."""
from __future__ import annotations

from elements import stroke

from typekernel.project import glyph
from typekernel.system import System


@glyph("w", group="lc.diag")
def w(system: System):
    st = float(system.stem["lc"])
    xh = float(system.zones.x)
    width = float(system.tokens.get("w_width", 560.0))
    lsb = float(system.tokens.get("lsb_lc", 32.0))
    x0 = lsb + st * 0.15
    x3 = lsb + width - st * 0.15
    x1 = x0 + (x3 - x0) / 3.0
    x2 = x0 + 2.0 * (x3 - x0) / 3.0
    return (
        stroke(system, [(x0, xh), (x1, 0.0)], thickness=st)
        + stroke(system, [(x1, 0.0), ((x1 + x2) / 2.0, xh * 0.55)], thickness=st)
        + stroke(system, [((x1 + x2) / 2.0, xh * 0.55), (x2, 0.0)], thickness=st)
        + stroke(system, [(x2, 0.0), (x3, xh)], thickness=st)
    )
