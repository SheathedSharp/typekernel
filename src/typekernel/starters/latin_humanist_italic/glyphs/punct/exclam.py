"""exclam — stem + period (skeleton+pen)."""

from __future__ import annotations

from elements import oval_points, stroke

from typekernel.project import glyph
from typekernel.system import System


@glyph("exclam", group="punct")
def exclam(system: System):
    st = float(system.stem["lc"])
    xh = float(system.zones.x)
    lsb = float(system.tokens.get("lsb_lc", 36.0)) * 0.6
    x = lsb + st * 0.5
    stem = stroke(system, [(x, st * 1.6), (x, xh)], thickness=st)
    r = st * 0.42
    dot = stroke(system, oval_points(x, r, r, r, n=12), closed=True, thickness=st * 0.85)
    return stem + dot
