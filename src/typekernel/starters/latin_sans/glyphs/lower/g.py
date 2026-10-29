"""Round glyph g — binocular: o-like bowl + ear stem + descender bowl."""

from __future__ import annotations

from elements import WIDTHS, bowl, stem_rect

from typekernel.project import glyph
from typekernel.system import System


@glyph("g", group="lc.round")
def g(system: System):
    st = float(system.stem["lc"])
    xh = float(system.zones.x)
    desc = float(system.zones.desc)
    width = float(WIDTHS["g"])
    lsb = float(system.tokens.get("lsb_lc", 40.0))
    ov = float(system.overshoot.round)

    # Upper bowl: same zone/overshoot recipe as o, inset so the ear overlaps
    # its right wall (a-style stem+bowl overlap).
    upper_rx = (width - st * 0.35) / 2.0
    upper_cx = lsb + upper_rx
    upper = bowl(
        system,
        cx=upper_cx,
        cy=xh / 2.0,
        rx=upper_rx,
        ry=xh / 2.0 + ov,
        thickness=st,
    )

    lower_cy = desc / 2.0
    lower_ry = abs(desc) / 2.0 + ov * 0.35
    lower_rx = width / 2.0 * 0.88
    lower_cx = lsb + width / 2.0 - st * 0.1
    lower = bowl(
        system,
        cx=lower_cx,
        cy=lower_cy,
        rx=lower_rx,
        ry=lower_ry,
        thickness=st * 0.95,
    )

    # Ear bridges upper and lower bowls (overlap both; no heal).
    ear = stem_rect(
        lsb + width - st,
        lsb + width,
        lower_cy - lower_ry * 0.2,
        xh * 0.78,
        prefix="ear",
    )
    return upper + ear + lower
