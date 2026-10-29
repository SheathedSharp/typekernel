"""Figure 9 — upper oval + gapped descender (interpolation-safe)."""

from __future__ import annotations

from elements import oval_points, stroke

from typekernel.project import glyph
from typekernel.system import System

_OVAL_N = 48
_GAP = 50.0


@glyph("nine", group="figs")
def nine(system: System):
    st = float(system.stem["lc"])
    width = float(system.tokens.get("fig_width", 460.0))
    lsb = float(system.tokens["lsb_lc"])
    h = float(system.zones.cap) * 0.72
    cx = lsb + width * 0.48
    cy = h * 0.62
    rx = width * 0.32
    ry = h * 0.28
    bowl = stroke(
        system, oval_points(cx, cy, rx, ry, n=_OVAL_N), closed=True, thickness=st
    )
    x = lsb + width * 0.78
    stem = stroke(system, [(x, 0.0), (x, cy - ry - _GAP)], thickness=st)
    return bowl + stem
