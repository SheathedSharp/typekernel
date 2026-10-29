"""Round glyph e — anatomy open_bowl + BarSpec (P3-7; closes A-2 θ)."""

from __future__ import annotations

from elements import WIDTHS, zone_anchors

from typekernel.anatomy import BarSpec, open_bowl
from typekernel.project import glyph
from typekernel.system import System


@glyph("e", group="lc.round")
def e(system: System):
    st = float(system.stem["lc"])
    thin = float(system.stem.get("lc_h", st * 0.85))
    xh = float(system.zones.x)
    width = float(WIDTHS["e"])
    lsb = float(system.tokens.get("lsb_lc", 40.0))
    ov = float(system.overshoot.round)
    exp = float(system.tokens.get("bowl_exponent", 2.15))
    aperture = float(system.tokens.get("bowl_aperture", 0.42))
    tension = float(system.tokens.get("shoulder_tension", 0.55))
    bar_t = min(float(system.tokens.get("bar_thickness", thin)), thin)
    cx = lsb + width / 2.0
    cy = xh / 2.0
    # Sit the crossbar on the lower aperture lip so the upper eye seals
    # across Light / Regular / Bold (open_bowl bar band).
    outer_ry = xh / 2.0 + ov
    inner_ry = max(outer_ry - thin, 1.0)
    lip_y = cy - aperture * inner_ry
    bar_y = min(lip_y + bar_t * 0.15, cy - thin * 0.35)
    return zone_anchors(
        open_bowl(
                (cx, cy),
                width / 2.0,
                xh / 2.0,
                thick=st,
                thin=thin,
                aperture=aperture,
                bar=BarSpec(y=bar_y, thick=bar_t, inset=st * 0.2),
                open_side="right",
                exponent=exp,
                overshoot=ov,
                tension=tension,
            ),
        system,
        top='x', ogonek=True,
    )
