"""Control glyph o — anatomy bowl ."""

from __future__ import annotations

from elements import zone_anchors

from typekernel.anatomy import bowl
from typekernel.project import glyph
from typekernel.system import System


@glyph("o", group="lc.round")
def o(system: System):
    width = float(system.tokens["o_width"])
    lsb = float(system.tokens.get("lsb_lc", 40.0))
    xh = float(system.zones.x)
    ov = float(system.overshoot.round)
    st = float(system.stem["lc"])
    thin = float(system.stem.get("lc_h", st * 0.85))
    exp = float(system.tokens.get("bowl_exponent", 2.15))
    cx = lsb + width / 2.0
    cy = xh / 2.0
    rx = width / 2.0
    ry = xh / 2.0
    return zone_anchors(
        bowl(
                (cx, cy),
                rx,
                ry,
                thick=st,
                thin=thin,
                exponent=exp,
                overshoot=ov,
                name="bowl",
            ),
        system,
        top='x', ogonek=True,
    )
