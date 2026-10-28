"""Lowercase t — short stem + crossbar."""
from __future__ import annotations

from elements import stroke

from typekernel.project import glyph
from typekernel.system import System


@glyph("t", group="lc.straight")
def t(system: System):
    st = float(system.stem["lc"])
    xh = float(system.zones.x)
    lsb = float(system.tokens.get("lsb_lc", 32.0))
    x = lsb + st * 0.9
    top = xh + float(system.overshoot.round) * 0.6
    stem = stroke(system, [(x, 0.0), (x, top)], thickness=st)
    bar_y = xh * 0.78
    bar = stroke(
        system,
        [(x - st * 1.3, bar_y), (x + st * 1.4, bar_y)],
        thickness=float(system.stem["lc_h"]),
    )
    return stem + bar
