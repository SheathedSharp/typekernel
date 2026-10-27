"""Round glyph g — binocular: upper bowl + lower loop (geometric sans)."""

from __future__ import annotations

from elements import bowl, stem_rect

from typekernel.project import glyph
from typekernel.system import System


@glyph("g", group="lc.round")
def g(system: System):
    st = float(system.stem["lc"])
    xh = float(system.zones.x)
    desc = float(system.zones.desc)
    width = float(system.tokens["g_width"])
    lsb = float(system.tokens.get("lsb_lc", 40.0))
    ov = float(system.overshoot.round)
    # Upper bowl like o but slightly smaller, sitting on the baseline-ish.
    cx = lsb + width / 2.0
    upper_cy = xh * 0.55
    upper_ry = xh * 0.45 + ov * 0.5
    upper_rx = width / 2.0 * 0.92
    upper = bowl(
        system, cx=cx, cy=upper_cy, rx=upper_rx, ry=upper_ry, thickness=st
    )
    # Right ear/stem linking upper to lower loop.
    ear = stem_rect(
        lsb + width - st, lsb + width, desc + abs(desc) * 0.35, xh * 0.85, prefix="ear"
    )
    # Lower loop (bowl) in the descender.
    lower_cy = desc / 2.0
    lower_ry = abs(desc) / 2.0 + ov * 0.4
    lower_rx = width / 2.0 * 0.85
    lower = bowl(
        system,
        cx=cx - st * 0.15,
        cy=lower_cy,
        rx=lower_rx,
        ry=lower_ry,
        thickness=st * 0.95,
    )
    return upper + ear + lower
