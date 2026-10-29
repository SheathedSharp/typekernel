"""n-group glyph r — stem + short arch stub."""

from __future__ import annotations

from elements import stroke

from typekernel.project import glyph
from typekernel.system import System


@glyph("r", group="lc.straight")
def r(system: System):
    st = float(system.stem["lc"])
    xh = float(system.zones.x)
    width = float(system.tokens.get("r_width", 300.0))
    lsb = float(system.tokens["lsb_lc"])
    x0 = lsb + st * 0.5
    x1 = lsb + width - st * 0.25
    stem = stroke(system, [(x0, 0.0), (x0, xh)], thickness=st)
    arch = stroke(
        system,
        [
            (x0, xh * 0.55),
            (x0, xh),
            ((x0 + x1) / 2.0, xh + st * 0.1),
            (x1, xh * 0.85),
        ],
        thickness=st * 0.95,
    )
    return stem + arch
