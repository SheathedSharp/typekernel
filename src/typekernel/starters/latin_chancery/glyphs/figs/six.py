"""Figure 6 — open bowl + lower nest."""
from __future__ import annotations
from elements import bowl, open_bowl
from typekernel.project import glyph
from typekernel.system import System

@glyph("six", group="figs")
def six(system: System):
    st = float(system.stem["lc"])
    width = float(system.tokens.get("fig_width", 420.0))
    lsb = float(system.tokens.get("lsb_lc", 32.0))
    h = float(system.zones.cap) * 0.72
    cx = lsb + width / 2.0
    spine = open_bowl(
        system, cx=cx, cy=h * 0.55, rx=width * 0.4, ry=h * 0.42,
        thickness=st, open_side="right", aperture_deg=55.0,
    )
    loop = bowl(system, cx=cx, cy=h * 0.32, rx=width * 0.34, ry=h * 0.28, thickness=st)
    return spine + loop
