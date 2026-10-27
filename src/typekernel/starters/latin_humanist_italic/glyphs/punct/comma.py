"""comma — period with tail (skeleton+pen)."""

from __future__ import annotations

from elements import oval_points, stroke

from typekernel.project import glyph
from typekernel.system import System


@glyph("comma", group="punct")
def comma(system: System):
    st = float(system.stem["lc"])
    r = st * 0.42
    lsb = float(system.tokens.get("lsb_lc", 36.0)) * 0.5
    cx = lsb + r
    head = stroke(system, oval_points(cx, r * 1.1, r, r, n=12), closed=True, thickness=st * 0.85)
    tail = stroke(system, [(cx + r * 0.2, r * 0.3), (cx - r * 0.6, -st * 0.9)], thickness=st * 0.75)
    return head + tail
