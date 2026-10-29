"""Round glyph G — anatomy open_bowl + spur bar ."""

from __future__ import annotations

from elements import WIDTHS, zone_anchors

from typekernel.anatomy import crossbar, open_bowl
from typekernel.project import glyph
from typekernel.system import System


@glyph("G", group="uc.round")
def glyph_G(system: System):
    st = float(system.stem["uc"])
    thin = float(system.stem.get("uc_h", st * 0.85))
    cap = float(system.zones.cap)
    width = float(WIDTHS["G"])
    lsb = float(system.tokens.get("lsb_uc", 50.0))
    ov = float(system.overshoot.round)
    exp = float(system.tokens.get("bowl_exponent", 2.15))
    aperture = float(system.tokens.get("bowl_aperture", 0.42))
    tension = float(system.tokens.get("shoulder_tension", 0.55))
    bar_t = float(system.tokens.get("bar_thickness", thin))
    cx = lsb + width / 2.0
    cy = cap / 2.0
    body = open_bowl(
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
    )
    spur = crossbar(
        cx,
        lsb + width - st * 0.15,
        cap * 0.42,
        thick=bar_t,
        name="spur",
        ends="none",
    )
    return zone_anchors(body + spur, system, top='cap')
