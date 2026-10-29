"""n-group glyph h — n-body + ascender tip (gap join; G-class)."""

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
    lsb = float(system.tokens["lsb_lc"])
    rise = float(system.tokens.get("arch_rise", 0.12)) * xh
    x0 = lsb + st * 0.5
    x1 = lsb + width - st * 0.5
    mid = (x0 + x1) / 2.0
    body = stroke(
        system,
        [
            (x0, 0.0),
            (x0, xh - rise),
            (x0 + (x1 - x0) * 0.15, xh),
            (mid, xh + rise * 0.15),
            (x1 - (x1 - x0) * 0.15, xh),
            (x1, xh - rise),
            (x1, 0.0),
        ],
        thickness=st,
    )
    tip = stroke(system, [(x0, xh + 60.0), (x0, asc)], thickness=st)
    return body + tip
