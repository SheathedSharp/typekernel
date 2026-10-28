"""Lowercase e — open bowl (chancery aperture), not a closed ring."""

from __future__ import annotations

from elements import stroke

from typekernel.project import glyph
from typekernel.system import System


@glyph("e", group="lc.round")
def e(system: System):
    st = float(system.stem["lc"])
    xh = float(system.zones.x)
    width = float(system.tokens["e_width"])
    lsb = float(system.tokens.get("lsb_lc", 32.0))
    ov = float(system.overshoot.round)
    cx = lsb + width * 0.5
    cy = xh * 0.5
    rx = width * 0.5 - st * 0.1
    ry = xh * 0.5 + ov * 0.5
    # Open C-like bowl: leave a gap on the right for aperture.
    import math

    pts = []
    a0, a1 = math.radians(-40), math.radians(220)
    n = 36
    for i in range(n):
        a = a0 + (a1 - a0) * i / (n - 1)
        pts.append((cx + rx * math.cos(a), cy + ry * math.sin(a)))
    # Crossbar through the counter.
    bar_y = cy + ry * 0.05
    bar = [
        (cx - rx * 0.55, bar_y),
        (cx + rx * 0.35, bar_y),
    ]
    return stroke(system, pts, thickness=st) + stroke(system, bar, thickness=float(system.stem["lc_h"]))
