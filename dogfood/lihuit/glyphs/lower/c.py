"""Round glyph c — anatomy open_bowl, aperture on the right (P3-7)."""

from __future__ import annotations

from elements import WIDTHS, zone_anchors

from typekernel.anatomy import open_bowl
from typekernel.project import glyph
from typekernel.system import System


@glyph("c", group="lc.round")
def c(system: System):
    st = float(system.stem["lc"])
    thin = float(system.stem.get("lc_h", st * 0.85))
    xh = float(system.zones.x)
    width = float(WIDTHS["c"])
    lsb = float(system.tokens.get("lsb_lc", 40.0))
    ov = float(system.overshoot.round)
    exp = float(system.tokens.get("bowl_exponent", 2.15))
    aperture = float(system.tokens.get("bowl_aperture", 0.42))
    tension = float(system.tokens.get("shoulder_tension", 0.55))
    cx = lsb + width / 2.0
    cy = xh / 2.0
    return zone_anchors(
        open_bowl(
                (cx, cy),
                width / 2.0,
                xh / 2.0,
                thick=st,
                thin=thin,
                aperture=aperture,
                open_side="right",
                exponent=exp,
                overshoot=ov,
                tension=tension,
            ),
        system,
        top='x',
    )
