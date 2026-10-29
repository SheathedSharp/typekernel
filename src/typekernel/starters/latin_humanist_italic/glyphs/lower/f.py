"""f — ascender stem + crossbar (skeleton+pen)."""

from __future__ import annotations

from elements import stroke

from typekernel.project import glyph
from typekernel.system import System


@glyph("f", group="lc.straight")
def f(system: System):
    st = float(system.stem["lc"])
    xh = float(system.zones.x)
    asc = float(system.zones.asc)
    width = float(system.tokens.get("f_width", 260.0))
    lsb = float(system.tokens.get("lsb_lc", 36.0))
    x = lsb + st * 0.55
    stem = stroke(
        system,
        [
            (x, 0.0),
            (x, asc - st * 0.8),
            (x + width * 0.35, asc),
            (x + width * 0.75, asc - st * 0.15),
        ],
        thickness=st,
    )
    bar_y = xh * 0.72
    bar = stroke(
        system,
        [(lsb, bar_y), (lsb + width, bar_y)],
        thickness=st * 0.85,
    )
    return stem + bar
