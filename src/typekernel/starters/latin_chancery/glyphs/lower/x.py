"""x — separated mild diags (G-class)."""

from __future__ import annotations

from elements import stroke

from typekernel.project import glyph
from typekernel.system import System


@glyph("x", group="lc.diag")
def x(system: System):
    st = float(system.stem["lc"])
    xh = float(system.zones.x)
    width = float(system.tokens.get("x_width", 400.0))
    lsb = float(system.tokens.get("lsb_lc", 32.0))
    x0 = lsb + st * 0.25
    x1 = lsb + width - st * 0.25
    mid = (x0 + x1) / 2.0
    gap = 35.0
    return (
        stroke(system, [(x0, xh), (mid - gap, xh * 0.5)], thickness=st)
        + stroke(system, [(mid + gap, xh * 0.5), (x1, 0.0)], thickness=st)
        + stroke(system, [(x1, xh), (mid + gap, xh * 0.5)], thickness=st)
        + stroke(system, [(mid - gap, xh * 0.5), (x0, 0.0)], thickness=st)
    )
