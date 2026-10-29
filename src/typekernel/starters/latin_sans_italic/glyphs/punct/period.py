"""period — baseline dot (interpolation-safe: thin oval, fixed n)."""

from __future__ import annotations

from elements import oval_points, stroke

from typekernel.project import glyph
from typekernel.system import System

_DOT_N = 16


@glyph("period", group="punct")
def period(system: System):
    st = float(system.stem["lc"])
    r = st * 0.55
    lsb = float(system.tokens["lsb_lc"]) * 0.5
    cx = lsb + r
    return stroke(
        system, oval_points(cx, r, r, r, n=_DOT_N), closed=True, thickness=st * 0.4
    )
