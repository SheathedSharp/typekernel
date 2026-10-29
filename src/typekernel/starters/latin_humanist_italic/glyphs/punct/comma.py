"""comma — period head + gapped tail (interpolation-safe)."""

from __future__ import annotations

from elements import oval_points, stroke

from typekernel.project import glyph
from typekernel.system import System

_DOT_N = 16


@glyph("comma", group="punct")
def comma(system: System):
    st = float(system.stem["lc"])
    r = st * 0.55
    lsb = float(system.tokens.get("lsb_lc", 36.0)) * 0.5
    cx = lsb + r
    head = stroke(
        system,
        oval_points(cx, r * 1.1, r, r, n=_DOT_N),
        closed=True,
        thickness=st * 0.4,
    )
    # Gap below head (≥30) so mid-lerp does not self-intersect.
    y0 = r * 1.1 - r - 35.0
    tail = stroke(
        system,
        [(cx + r * 0.1, y0), (cx - r * 0.5, y0 - st * 0.9)],
        thickness=st * 0.55,
    )
    return head + tail
