"""Mixed glyph R — anatomy stem + bowl + diagonal leg ."""

from __future__ import annotations

from elements import WIDTHS, zone_anchors

from typekernel.anatomy import bowl, stem
from typekernel.draw import Writer, diagonal_band
from typekernel.project import glyph
from typekernel.system import System


@glyph("R", group="uc.mixed")
def glyph_R(system: System):
    st = float(system.stem["uc"])
    thin = float(system.stem.get("uc_h", st * 0.85))
    cap = float(system.zones.cap)
    width = float(WIDTHS["R"])
    lsb = float(system.tokens.get("lsb_uc", 50.0))
    ov = float(system.overshoot.round) * 0.4
    exp = float(system.tokens.get("bowl_exponent", 2.15))
    left = stem(lsb, lsb + st, 0.0, cap, name="stem.l")
    cx = lsb + st + (width - st) * 0.45
    ring = bowl(
        (cx, cap * 0.70),
        (width - st) * 0.48,
        cap * 0.30,
        thick=st,
        thin=thin,
        exponent=exp,
        overshoot=ov,
        name="bowl",
    )
    join_y = cap * 0.42
    band_l, band_r = diagonal_band(
        (lsb + st * 0.7, join_y),
        (lsb + width - st * 0.2, 0.0),
        weight=st,
        compensate=True,
    )
    leg = (
        Writer()
        .start(band_l.start)
        .corner("diag.top.l")
        .fragment(band_l)
        .corner("diag.foot.l")
        .line(band_r.start)
        .corner("diag.foot.r")
        .fragment(band_r)
        .corner("diag.top.r")
        .line(band_l.start)
        .close()
        .build()
    )
    return zone_anchors(left + ring + leg, system, top='cap')
