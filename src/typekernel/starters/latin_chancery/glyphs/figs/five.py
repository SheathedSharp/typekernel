"""Figure 5 — flag + open bowl."""
from __future__ import annotations

from elements import open_bowl, stroke

from typekernel.project import glyph
from typekernel.system import System


@glyph("five", group="figs")
def five(system: System):
    st = float(system.stem["lc"])
    width = float(system.tokens.get("fig_width", 420.0))
    lsb = float(system.tokens.get("lsb_lc", 32.0))
    h = float(system.zones.cap) * 0.72
    top = stroke(
        system, [(lsb + width * 0.85, h), (lsb + st * 0.4, h), (lsb + st * 0.4, h * 0.55)],
        thickness=st,
    )
    bowl = open_bowl(
        system, cx=lsb + width * 0.5, cy=h * 0.32, rx=width * 0.4, ry=h * 0.3,
        thickness=st, open_side="left", aperture_deg=95.0,
    )
    return top + bowl
