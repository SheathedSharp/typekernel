"""Round glyph D — anatomy stem + bowl ."""

from __future__ import annotations

from elements import WIDTHS, zone_anchors

from typekernel.anatomy import bowl, stem
from typekernel.project import glyph
from typekernel.system import System


@glyph("D", group="uc.round")
def glyph_D(system: System):
    st = float(system.stem["uc"])
    thin = float(system.stem.get("uc_h", st * 0.85))
    cap = float(system.zones.cap)
    width = float(WIDTHS["D"])
    lsb = float(system.tokens.get("lsb_uc", 50.0))
    ov = float(system.overshoot.round)
    exp = float(system.tokens.get("bowl_exponent", 2.15))
    left = stem(lsb, lsb + st, 0.0, cap, name="stem.l")
    cx = lsb + st + (width - st) / 2.0
    cy = cap / 2.0
    rx = (width - st) / 2.0 + st * 0.35
    ring = bowl(
        (cx, cy),
        rx,
        cap / 2.0,
        thick=st,
        thin=thin,
        exponent=exp,
        overshoot=ov,
        name="bowl",
    )
    return zone_anchors(left + ring, system, top='cap')
