"""Control glyph O — anatomy bowl ."""

from __future__ import annotations

from elements import zone_anchors

from typekernel.anatomy import bowl
from typekernel.project import glyph
from typekernel.system import System


@glyph("O", group="uc.round")
def glyph_O(system: System):
    width = float(system.tokens["O_width"])
    lsb = float(system.tokens.get("lsb_uc", 50.0))
    cap = float(system.zones.cap)
    ov = float(system.overshoot.round)
    st = float(system.stem["uc"])
    thin = float(system.stem.get("uc_h", st * 0.85))
    exp = float(system.tokens.get("bowl_exponent", 2.15))
    cx = lsb + width / 2.0
    cy = cap / 2.0
    rx = width / 2.0
    ry = cap / 2.0
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
        top='cap', ogonek=True,
    )
