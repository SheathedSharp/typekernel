"""period — baseline dot (skeleton+pen)."""

from __future__ import annotations

from elements import oval_points, stroke

from typekernel.project import glyph
from typekernel.system import System


@glyph("period", group="punct")
def period(system: System):
    st = float(system.stem["lc"])
    r = st * 0.45
    lsb = float(system.tokens.get("lsb_lc", 36.0)) * 0.5
    cx = lsb + r
    return stroke(system, oval_points(cx, r, r, r, n=12), closed=True, thickness=st * 0.9)
