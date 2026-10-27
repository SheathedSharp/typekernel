"""o-group glyph a — bowl + right stem (skeleton+pen)."""

from __future__ import annotations

from elements import oval_points, stroke

from typekernel.project import glyph
from typekernel.system import System


@glyph("a", group="lc.bowl")
def a(system: System):
    st = float(system.stem["lc"])
    xh = float(system.zones.x)
    width = float(system.tokens.get("o_width", 420.0)) * 0.95
    lsb = float(system.tokens.get("lsb_lc", 36.0))
    ov = float(system.overshoot.round)
    x_stem = lsb + width - st * 0.5
    stem_d = stroke(system, [(x_stem, 0.0), (x_stem, xh)], thickness=st)
    cx = lsb + width * 0.42
    cy = xh * 0.48
    rx = width * 0.36
    ry = xh * 0.42 + ov * 0.35
    bowl = stroke(system, oval_points(cx, cy, rx, ry), closed=True, thickness=st)
    return stem_d + bowl
