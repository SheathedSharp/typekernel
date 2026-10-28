"""Lowercase y — v body into descender."""
from __future__ import annotations

from elements import stroke

from typekernel.project import glyph
from typekernel.system import System


@glyph("y", group="lc.diag")
def y(system: System):
    st = float(system.stem["lc"])
    xh = float(system.zones.x)
    desc = float(system.zones.desc)
    width = float(system.tokens.get("y_width", 360.0))
    lsb = float(system.tokens.get("lsb_lc", 32.0))
    x0 = lsb + st * 0.2
    x1 = lsb + width - st * 0.2
    mid = (x0 + x1) / 2.0
    return (
        stroke(system, [(x0, xh), (mid, 0.0)], thickness=st)
        + stroke(system, [(x1, xh), (mid, 0.0)], thickness=st)
        + stroke(system, [(mid, 0.0), (mid - st * 0.4, desc)], thickness=st)
    )
