"""w — twin open cups with mid gap (interpolation-safe; continuous double-v self-intersection)."""

from __future__ import annotations

from elements import fuse, stroke

from typekernel.project import glyph
from typekernel.system import System


@glyph("w", group="lc.diag")
def w(system: System):
    st = float(system.stem["lc"])
    xh = float(system.zones.x)
    width = float(system.tokens.get("w_width", 620.0))
    lsb = float(system.tokens.get("lsb_lc", 32.0))
    x0 = lsb + st * 0.4
    x1 = lsb + width * 0.35
    x2 = lsb + width * 0.65
    x3 = lsb + width - st * 0.4
    left = fuse(stroke(system, [(x0, xh), (x0, 0.0), (x1, 0.0), (x1, xh * 0.55)], thickness=st))
    right = fuse(stroke(system, [(x2, xh * 0.55), (x2, 0.0), (x3, 0.0), (x3, xh)], thickness=st))
    return left + right
