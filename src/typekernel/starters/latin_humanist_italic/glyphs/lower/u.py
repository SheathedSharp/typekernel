"""n-group glyph u — mirrored arch skeleton (broad nib)."""

from __future__ import annotations

from elements import stroke

from typekernel.project import glyph
from typekernel.system import System


@glyph("u", group="lc.straight")
def u(system: System):
    st = float(system.stem["lc"])
    xh = float(system.zones.x)
    width = float(system.tokens["n_width"])
    lsb = float(system.tokens.get("lsb_lc", 36.0))
    rise = float(system.tokens.get("arch_rise", 0.12)) * xh
    x0 = lsb + st * 0.5
    x1 = lsb + width - st * 0.5
    mid = (x0 + x1) / 2.0
    points = [
        (x0, xh),
        (x0, rise),
        (x0 + (x1 - x0) * 0.15, 0.0),
        (mid, -rise * 0.15),
        (x1 - (x1 - x0) * 0.15, 0.0),
        (x1, rise),
        (x1, xh),
    ]
    return stroke(system, points, thickness=st)
