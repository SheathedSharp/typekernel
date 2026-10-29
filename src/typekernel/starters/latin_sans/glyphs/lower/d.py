"""Round glyph d — anatomy bowl + ascender stem ."""

from __future__ import annotations

from elements import zone_anchors

from typekernel.anatomy import bowl, stem
from typekernel.project import glyph
from typekernel.system import System


@glyph("d", group="lc.round")
def d(system: System):
    st = float(system.stem["lc"])
    thin = float(system.stem.get("lc_h", st * 0.85))
    xh = float(system.zones.x)
    asc = float(system.zones.asc)
    ov = float(system.overshoot.round)
    width = float(system.tokens["o_width"])
    lsb = float(system.tokens.get("lsb_lc", 40.0))
    exp = float(system.tokens.get("bowl_exponent", 2.15))
    right = stem(lsb + width - st, lsb + width, 0.0, asc, name="stem.r")
    cx = lsb + width / 2.0
    cy = xh / 2.0
    ring = bowl(
        (cx, cy),
        width / 2.0,
        xh / 2.0,
        thick=st,
        thin=thin,
        exponent=exp,
        overshoot=ov,
        name="bowl",
    )
    return zone_anchors(ring + right, system, top='x')
