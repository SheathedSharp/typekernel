"""z — top bar + diagonal + bottom bar (skeleton+pen)."""

from __future__ import annotations

from elements import stroke

from typekernel.project import glyph
from typekernel.system import System


@glyph("z", group="lc.diag")
def z(system: System):
    st = float(system.stem["lc"])
    xh = float(system.zones.x)
    width = float(system.tokens.get("z_width", 400.0))
    lsb = float(system.tokens.get("lsb_lc", 36.0))
    x0 = lsb
    x1 = lsb + width
    top = stroke(system, [(x0, xh), (x1, xh)], thickness=st)
    diag = stroke(system, [(x1, xh), (x0, 0.0)], thickness=st)
    bot = stroke(system, [(x0, 0.0), (x1, 0.0)], thickness=st)
    return top + diag + bot
