"""Lowercase z — zigzag."""
from __future__ import annotations
from elements import stroke
from typekernel.project import glyph
from typekernel.system import System

@glyph("z", group="lc.diag")
def z(system: System):
    st = float(system.stem["lc"])
    xh = float(system.zones.x)
    width = float(system.tokens.get("z_width", 340.0))
    lsb = float(system.tokens.get("lsb_lc", 32.0))
    x0 = lsb + st * 0.15
    x1 = lsb + width - st * 0.15
    thin = float(system.stem["lc_h"])
    return (
        stroke(system, [(x0, xh), (x1, xh)], thickness=thin)
        + stroke(system, [(x1, xh), (x0, 0.0)], thickness=st)
        + stroke(system, [(x0, 0.0), (x1, 0.0)], thickness=thin)
    )
