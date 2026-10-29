"""Mixed glyph S — stacked anatomy open_bowl pair ."""

from __future__ import annotations

from elements import WIDTHS, zone_anchors

from typekernel.anatomy import open_bowl
from typekernel.project import glyph
from typekernel.system import System


@glyph("S", group="uc.mixed")
def glyph_S(system: System):
    st = float(system.stem["uc"])
    thin = float(system.stem.get("uc_h", st * 0.85))
    cap = float(system.zones.cap)
    width = float(WIDTHS["S"])
    lsb = float(system.tokens.get("lsb_uc", 50.0))
    ov = float(system.overshoot.round)
    exp = float(system.tokens.get("bowl_exponent", 2.15))
    aperture = float(system.tokens.get("bowl_aperture", 0.42))
    tension = float(system.tokens.get("shoulder_tension", 0.55))
    cx = lsb + width / 2.0
    rx = width / 2.0 * 0.95
    overlap = st * 0.55
    ry = max(cap * 0.30, (cap + 2.0 * ov + overlap) / 4.0)
    upper = open_bowl(
        (cx, (cap + ov) - ry),
        rx,
        ry,
        thick=st,
        thin=thin,
        aperture=aperture,
        open_side="right",
        exponent=exp,
        overshoot=0.0,
        tension=tension,
        name="bowl.t",
        aperture_index=0,
    )
    lower = open_bowl(
        (cx, (-ov) + ry),
        rx,
        ry,
        thick=st,
        thin=thin,
        aperture=aperture,
        open_side="left",
        exponent=exp,
        overshoot=0.0,
        tension=tension,
        name="bowl.b",
        aperture_index=1,
    )
    return zone_anchors(upper + lower, system, top='cap')
