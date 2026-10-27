"""j — descender stem + tittle (skeleton+pen)."""

from __future__ import annotations

from elements import stroke

from typekernel.project import glyph
from typekernel.system import System


@glyph("j", group="lc.straight")
def j(system: System):
    st = float(system.stem["lc"])
    xh = float(system.zones.x)
    desc = float(system.zones.desc)
    lsb = float(system.tokens.get("lsb_lc", 36.0))
    x = lsb + st * 1.1
    # Stem with leftward hook; tip stays above desc - tol.
    tip_y = desc + st * 0.35
    stem = stroke(
        system,
        [
            (x, xh * 0.72),
            (x, desc + st * 0.85),
            (x - st * 1.1, tip_y),
            (x - st * 1.8, tip_y + st * 0.35),
        ],
        thickness=st,
    )
    cy = xh * 0.88
    r = st * 0.45
    dot = stroke(
        system,
        [(x, cy - r), (x + r, cy), (x, cy + r), (x - r, cy)],
        closed=True,
        thickness=st * 0.85,
    )
    return stem + dot
