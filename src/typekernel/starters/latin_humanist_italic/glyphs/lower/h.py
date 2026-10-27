"""n-group glyph h — slanted ascender stem + arch (broad nib)."""

from __future__ import annotations

from elements import stroke

from typekernel.project import glyph
from typekernel.system import System


@glyph("h", group="lc.straight")
def h(system: System):
    st = float(system.stem["lc"])
    xh = float(system.zones.x)
    asc = float(system.zones.asc)
    width = float(system.tokens["n_width"])
    lsb = float(system.tokens.get("lsb_lc", 36.0))
    rise = float(system.tokens.get("arch_rise", 0.12)) * xh
    x0 = lsb + st * 0.5
    x1 = lsb + width - st * 0.5
    mid = (x0 + x1) / 2.0
    # Left stem from ascender; arch at x-height; right stem to baseline.
    points = [
        (x0, asc),
        (x0, xh - rise),
        (x0 + (x1 - x0) * 0.15, xh),
        (mid, xh + rise * 0.15),
        (x1 - (x1 - x0) * 0.15, xh),
        (x1, xh - rise),
        (x1, 0.0),
    ]
    return stroke(system, points, thickness=st)
