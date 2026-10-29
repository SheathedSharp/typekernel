"""quotesingle — short vertical mark."""

from __future__ import annotations

from elements import stroke

from typekernel.project import glyph
from typekernel.system import System


@glyph("quotesingle", group="punct")
def quotesingle(system: System):
    st = float(system.stem["lc"])
    xh = float(system.zones.x)
    lsb = float(system.tokens["lsb_lc"]) * 0.5
    x = lsb + st * 0.4
    return stroke(system, [(x, xh * 0.72), (x, xh + st * 0.15)], thickness=st * 0.85)
