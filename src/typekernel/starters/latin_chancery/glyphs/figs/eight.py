"""Figure 8 — two stacked bowls."""
from __future__ import annotations
from elements import bowl
from typekernel.project import glyph
from typekernel.system import System

@glyph("eight", group="figs")
def eight(system: System):
    st = float(system.stem["lc"])
    width = float(system.tokens.get("fig_width", 420.0)) * 0.9
    lsb = float(system.tokens.get("lsb_lc", 32.0))
    h = float(system.zones.cap) * 0.72
    cx = lsb + width / 2.0
    upper = bowl(system, cx=cx, cy=h * 0.68, rx=width * 0.36, ry=h * 0.26, thickness=st)
    lower = bowl(system, cx=cx, cy=h * 0.3, rx=width * 0.4, ry=h * 0.3, thickness=st)
    return upper + lower
