"""Control n — stem + arch (skeleton+pen)."""

from __future__ import annotations

from elements import stroke

from typekernel.project import glyph
from typekernel.system import System


@glyph("n", group="control")
def n(system: System):
    st = float(system.stem["lc"])
    xh = float(system.zones.x)
    width = float(system.tokens["n_width"])
    lsb = float(system.tokens["lsb_lc"])
    x0 = lsb + st * 0.5
    x1 = lsb + width - st * 0.5
    left = stroke(system, [(x0, 0.0), (x0, xh)], thickness=st)
    right = stroke(system, [(x1, 0.0), (x1, xh * 0.55)], thickness=st)
    arch = stroke(
        system,
        [
            (x0, xh * 0.55),
            (x0, xh),
            ((x0 + x1) / 2.0, xh + st * 0.15),
            (x1, xh),
            (x1, xh * 0.55),
        ],
        thickness=st,
    )
    return left + arch + right
