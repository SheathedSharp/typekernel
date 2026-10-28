"""Figure 3 — stacked open bowls."""
from __future__ import annotations
from elements import open_bowl
from typekernel.project import glyph
from typekernel.system import System

@glyph("three", group="figs")
def three(system: System):
    st = float(system.stem["lc"])
    width = float(system.tokens.get("fig_width", 420.0)) * 0.9
    lsb = float(system.tokens.get("lsb_lc", 32.0))
    h = float(system.zones.cap) * 0.72
    cx = lsb + width / 2.0
    upper = open_bowl(
        system, cx=cx, cy=h * 0.7, rx=width * 0.4, ry=h * 0.26,
        thickness=st, open_side="left", aperture_deg=90.0,
    )
    lower = open_bowl(
        system, cx=cx, cy=h * 0.28, rx=width * 0.42, ry=h * 0.28,
        thickness=st, open_side="left", aperture_deg=90.0,
    )
    return upper + lower
