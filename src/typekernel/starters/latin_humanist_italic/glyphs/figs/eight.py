"""Figure 8 — single oval (interim G-class; dual bowls SI under Bold)."""

from __future__ import annotations

from elements import oval_points, stroke

from typekernel.project import glyph
from typekernel.system import System

_OVAL_N = 48


@glyph("eight", group="figs")
def eight(system: System):
    st = float(system.stem["lc"])
    width = float(system.tokens.get("fig_width", 460.0))
    lsb = float(system.tokens.get("lsb_lc", 36.0))
    h = float(system.zones.cap) * 0.72
    return stroke(
        system,
        oval_points(lsb + width / 2.0, h / 2.0, width * 0.35, h * 0.42, n=_OVAL_N),
        closed=True,
        thickness=st,
    )
