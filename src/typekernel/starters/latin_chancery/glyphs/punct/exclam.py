"""exclam — stem + pen_dot."""
from __future__ import annotations

from elements import pen_dot, stroke

from typekernel.project import glyph
from typekernel.system import System


@glyph("exclam", group="punct")
def exclam(system: System):
    st = float(system.stem["lc"])
    r = float(system.stem.get("lc_h", st)) * (float(system.tokens.get("dot_radius", 28.0)) / 36.0)
    xh = float(system.zones.x)
    lsb = float(system.tokens.get("lsb_lc", 32.0)) * 0.6
    x = lsb + st * 0.5
    stem = stroke(system, [(x, r * 3.2), (x, xh)], thickness=st)
    return stem + pen_dot(system, x, r * 0.9)
