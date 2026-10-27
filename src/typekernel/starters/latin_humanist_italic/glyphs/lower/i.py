"""n-group glyph i — short stem + tittle (overlaid)."""

from __future__ import annotations

from elements import stroke

from typekernel.project import glyph
from typekernel.system import System


@glyph("i", group="lc.straight")
def i(system: System):
    st = float(system.stem["lc"])
    xh = float(system.zones.x)
    lsb = float(system.tokens.get("lsb_lc", 36.0))
    x = lsb + st * 0.5
    stem = stroke(system, [(x, 0.0), (x, xh * 0.72)], thickness=st)
    # Dot as a short closed diamond-ish oval above the stem.
    cy = xh * 0.88
    r = st * 0.45
    dot = stroke(
        system,
        [
            (x, cy - r),
            (x + r, cy),
            (x, cy + r),
            (x - r, cy),
        ],
        closed=True,
        thickness=st * 0.85,
    )
    return stem + dot
