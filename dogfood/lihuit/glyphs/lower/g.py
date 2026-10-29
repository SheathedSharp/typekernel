"""Mixed glyph g — binocular bowls + ear stem (P3-7)."""

from __future__ import annotations

from elements import WIDTHS, zone_anchors

from typekernel.anatomy import bowl, stem
from typekernel.project import glyph
from typekernel.system import System


@glyph("g", group="lc.mixed")
def g(system: System):
    st = float(system.stem["lc"])
    thin = float(system.stem.get("lc_h", st * 0.85))
    xh = float(system.zones.x)
    desc = float(system.zones.desc)
    width = float(WIDTHS["g"])
    lsb = float(system.tokens.get("lsb_lc", 40.0))
    ov = float(system.overshoot.round)
    exp = float(system.tokens.get("bowl_exponent", 2.15))

    upper_rx = (width - st * 0.35) / 2.0
    upper_cx = lsb + upper_rx
    upper = bowl(
        (upper_cx, xh / 2.0),
        upper_rx,
        xh / 2.0,
        thick=st,
        thin=thin,
        exponent=exp,
        overshoot=ov,
        name="bowl.t",
    )

    lower_cy = desc / 2.0
    lower_ry = abs(desc) / 2.0
    lower_rx = width / 2.0 * 0.88
    lower_cx = lsb + width / 2.0 - st * 0.1
    lower = bowl(
        (lower_cx, lower_cy),
        lower_rx,
        lower_ry,
        thick=st * 0.95,
        thin=thin * 0.95,
        exponent=exp,
        overshoot=ov * 0.35,
        name="bowl.b",
    )

    ear = stem(
        lsb + width - st,
        lsb + width,
        lower_cy - lower_ry * 0.2,
        xh * 0.78,
        name="stem.r",
        foot="none",
        top="none",
    )
    return zone_anchors(upper + ear + lower, system, top='x')
