"""Figure 6 — lower oval + gapped upright (G-class)."""

from __future__ import annotations

from elements import oval_points, stroke

from typekernel.project import glyph
from typekernel.system import System

_OVAL_N = 48
_GAP = 50.0


@glyph("six", group="figs")
def six(system: System):
    st = float(system.stem["lc"])
    width = float(system.tokens.get("fig_width", 460.0))
    lsb = float(system.tokens.get("lsb_lc", 36.0))
    h = float(system.zones.cap) * 0.72
    cx = lsb + width * 0.55
    cy = h * 0.32
    rx = width * 0.32
    ry = h * 0.28
    bowl = stroke(
        system, oval_points(cx, cy, rx, ry, n=_OVAL_N), closed=True, thickness=st
    )
    x = lsb + width * 0.22
    stem = stroke(system, [(x, cy + ry + _GAP), (x, h)], thickness=st)
    return bowl + stem
