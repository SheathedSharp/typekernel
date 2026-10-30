"""y — v-join with descender (skeleton+pen)."""

from __future__ import annotations

from elements import WIDTHS, diagonal_stroke, fuse

from typekernel.project import glyph
from typekernel.system import System


@glyph("y", group="lc.diag")
def y(system: System):
    st = float(system.stem["lc"])
    xh = float(system.zones.x)
    desc = float(system.zones.desc)
    width = float(WIDTHS.get("y", 400.0))
    lsb = float(system.tokens.get("lsb_lc", 36.0))
    x0 = lsb + st * 0.3
    x1 = lsb + width - st * 0.3
    mid = (x0 + x1) / 2.0
    left = diagonal_stroke(system, [(x0, xh), (mid, xh * 0.15)], thickness=st)
    right = diagonal_stroke(
        system,
        [(x1, xh), (mid, xh * 0.15), (mid - st * 0.4, desc)],
        thickness=st,
    )
    return fuse(left + right)
