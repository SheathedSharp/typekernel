"""Mixed glyph g — double-storey: upper bowl + right stem + lower bowl.

Letter-class topology: 2 counters, 1 island (binocular sans g). The stem
seals the upper ring like ``a`` and links into the descender loop so a third
cavity does not form between the bowls.
"""

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

    # Shared vertical like ``a``: stem from near-descender up through x-height.
    right = stem(
        lsb + width - st,
        lsb + width,
        desc * 0.15,
        xh,
        name="stem.r",
        foot="none",
        top="none",
    )

    bowl_w = width - st * 0.55
    cx = lsb + bowl_w / 2.0
    upper = bowl(
        (cx, xh * 0.48),
        bowl_w / 2.0,
        xh * 0.48,
        thick=st,
        thin=thin,
        exponent=exp,
        overshoot=ov * 0.5,
        name="bowl.t",
    )

    lower_cy = desc / 2.0
    lower_ry = abs(desc) / 2.0
    lower = bowl(
        (cx, lower_cy),
        bowl_w / 2.0 * 0.92,
        lower_ry,
        thick=st * 0.9,
        thin=thin * 0.9,
        exponent=exp,
        overshoot=ov * 0.3,
        name="bowl.b",
    )
    return zone_anchors(upper + right + lower, system, top="x")
