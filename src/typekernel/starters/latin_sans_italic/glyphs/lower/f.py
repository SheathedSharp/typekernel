"""f — continuous ascender with top flag + right-only crossbar (interpolation-safe)."""

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
    lsb = float(system.tokens["lsb_lc"])
    x = lsb + st * 0.55
    stem = stroke(
        system,
        [(x, 0.0), (x, asc - st * 0.25), (x + width * 0.55, asc)],
        thickness=st,
    )
    by = xh * 0.55
    bar = stroke(
        system,
        [(x + st * 1.2, by), (lsb + width, by)],
        thickness=st * 0.85,
    )
    return stem + bar
