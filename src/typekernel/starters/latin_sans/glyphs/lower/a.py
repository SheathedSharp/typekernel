"""Mixed glyph a — anatomy bowl + right stem (P3-7)."""

from __future__ import annotations

from elements import WIDTHS

from typekernel.anatomy import bowl, stem
from typekernel.project import glyph
from typekernel.system import System


@glyph("a", group="lc.mixed")
def a(system: System):
    st = float(system.stem["lc"])
    thin = float(system.stem.get("lc_h", st * 0.85))
    xh = float(system.zones.x)
    width = float(WIDTHS["a"])
    lsb = float(system.tokens.get("lsb_lc", 40.0))
    ov = float(system.overshoot.round)
    exp = float(system.tokens.get("bowl_exponent", 2.15))
    right = stem(lsb + width - st, lsb + width, 0.0, xh, name="stem.r")
    bowl_w = width - st * 0.55
    cx = lsb + bowl_w / 2.0
    cy = xh * 0.48
    ring = bowl(
        (cx, cy),
        bowl_w / 2.0,
        xh * 0.48,
        thick=st,
        thin=thin,
        exponent=exp,
        overshoot=ov * 0.5,
        name="bowl",
    )
    return ring + right
