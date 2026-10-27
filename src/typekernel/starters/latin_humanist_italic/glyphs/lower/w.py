"""w — double-v diagonals (skeleton+pen)."""

from __future__ import annotations

from elements import stroke

from typekernel.project import glyph
from typekernel.system import System


@glyph("w", group="lc.diag")
def w(system: System):
    st = float(system.stem["lc"])
    xh = float(system.zones.x)
    width = float(system.tokens.get("w_width", 620.0))
    lsb = float(system.tokens.get("lsb_lc", 36.0))
    x0 = lsb + st * 0.25
    x3 = lsb + width - st * 0.25
    x1 = lsb + width * 0.35
    x2 = lsb + width * 0.65
    mid_top = (x1 + x2) / 2.0
    return (
        stroke(system, [(x0, xh), (x1, 0.0)], thickness=st)
        + stroke(system, [(x1, 0.0), (mid_top, xh * 0.55)], thickness=st)
        + stroke(system, [(mid_top, xh * 0.55), (x2, 0.0)], thickness=st)
        + stroke(system, [(x2, 0.0), (x3, xh)], thickness=st)
    )
