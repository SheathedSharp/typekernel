"""colon — two anatomy dots ."""

from __future__ import annotations

from typekernel.anatomy import dot
from typekernel.project import glyph
from typekernel.system import System


@glyph("colon", group="punct")
def colon(system: System):
    st = float(system.stem["lc"])
    xh = float(system.zones.x)
    size = st * 0.9
    lsb = float(system.tokens.get("lsb_lc", 40.0)) * 0.5
    cx = lsb + size / 2.0
    bot = dot((cx, size / 2.0), size, shape="square", name="dot.b")
    top = dot((cx, xh - size / 2.0), size, shape="square", name="dot.t")
    return bot + top
