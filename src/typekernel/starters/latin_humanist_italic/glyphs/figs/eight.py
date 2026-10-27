"""Figure 8 — stacked ovals (skeleton+pen)."""

from __future__ import annotations

from elements import oval_points, stroke

from typekernel.project import glyph
from typekernel.system import System


@glyph("eight", group="figs")
def eight(system: System):
    st = float(system.stem["lc"])
    width = float(system.tokens.get("fig_width", 460.0))
    lsb = float(system.tokens.get("lsb_lc", 36.0))
    h = float(system.zones.cap) * 0.72
    cx = lsb + width / 2.0
    upper = stroke(
        system,
        oval_points(cx, h * 0.68, width * 0.34, h * 0.26),
        closed=True,
        thickness=st,
    )
    lower = stroke(
        system,
        oval_points(cx, h * 0.30, width * 0.38, h * 0.30),
        closed=True,
        thickness=st,
    )
    return upper + lower
