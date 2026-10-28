"""Lowercase f — tall stem + crossbar + entry flourish."""
from __future__ import annotations

from elements import flourish_entry, stroke, stroke_fragment

from typekernel.project import glyph
from typekernel.system import System


@glyph("f", group="lc.straight")
def f(system: System):
    st = float(system.stem["lc"])
    xh = float(system.zones.x)
    asc = float(system.zones.asc)
    lsb = float(system.tokens.get("lsb_lc", 32.0))
    x = lsb + st * 1.1
    stem = stroke(system, [(x, 0.0), (x, asc - 55.0)], thickness=st)
    bar_y = xh * 0.92
    bar = stroke(
        system,
        [(x - st * 1.2, bar_y), (x + st * 1.6, bar_y)],
        thickness=float(system.stem["lc_h"]),
    )
    frag = flourish_entry(system, (x - 70.0, asc - 40.0), (x, asc - 55.0))
    return stem + bar + stroke_fragment(system, frag, thickness=float(system.stem["lc_h"]))
