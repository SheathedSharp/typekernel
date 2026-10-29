"""Round glyph C — anatomy open_bowl at cap height (P3-7)."""

from __future__ import annotations

from elements import WIDTHS, zone_anchors

from typekernel.anatomy import open_bowl
from typekernel.project import glyph
from typekernel.system import System


@glyph("C", group="uc.round")
def glyph_C(system: System):
    st = float(system.stem["uc"])
    thin = float(system.stem.get("uc_h", st * 0.85))
    cap = float(system.zones.cap)
    width = float(WIDTHS["C"])
    lsb = float(system.tokens.get("lsb_uc", 50.0))
    ov = float(system.overshoot.round)
    exp = float(system.tokens.get("bowl_exponent", 2.15))
    aperture = float(system.tokens.get("bowl_aperture", 0.42))
    tension = float(system.tokens.get("shoulder_tension", 0.55))
    cx = lsb + width / 2.0
    cy = cap / 2.0
    return zone_anchors(
        open_bowl(
                (cx, cy),
                width / 2.0,
                cap / 2.0,
                thick=st,
                thin=thin,
                aperture=aperture,
                open_side="right",
                exponent=exp,
                overshoot=ov,
                tension=tension,
            ),
        system,
        top='cap',
    )
