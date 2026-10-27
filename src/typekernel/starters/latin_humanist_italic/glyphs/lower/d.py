"""o-group glyph d — slanted stem + oval bowl (skeleton+pen)."""

from __future__ import annotations

from elements import oval_points, stroke

from typekernel.project import glyph
from typekernel.system import System


@glyph("d", group="lc.bowl")
def d(system: System):
    st = float(system.stem["lc"])
    xh = float(system.zones.x)
    asc = float(system.zones.asc)
    desc = float(system.zones.desc)
    width = float(system.tokens.get("o_width", 420.0))
    lsb = float(system.tokens.get("lsb_lc", 36.0))
    ov = float(system.overshoot.round)

    # Ascender stem on the right; bowl to the left.
    x_stem = lsb + width - st * 0.5
    stem_d = stroke(system, [(x_stem, 0.0), (x_stem, asc)], thickness=st)
    cx = lsb + width * 0.42
    cy = xh / 2.0
    rx = width * 0.38
    ry = xh / 2.0 + ov * 0.5
    bowl = stroke(system, oval_points(cx, cy, rx, ry), closed=True, thickness=st)
    return stem_d + bowl

