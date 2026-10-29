"""z — fused bars + diagonal (G-class)."""

from __future__ import annotations

from elements import fuse, stroke

from typekernel.project import glyph
from typekernel.system import System


@glyph("z", group="lc.diag")
def z(system: System):
    st = float(system.stem["lc"])
    xh = float(system.zones.x)
    width = float(system.tokens.get("z_width", 400.0))
    lsb = float(system.tokens.get("lsb_lc", 32.0))
    x0, x1 = lsb, lsb + width
    return fuse(stroke(system, [(x0, xh), (x1, xh), (x0, 0.0), (x1, 0.0)], thickness=st))
