"""Figure 9 — bowl with overlapping lower open spine."""

from __future__ import annotations

from elements import bowl, open_bowl

from typekernel.project import glyph
from typekernel.system import System


@glyph("nine", group="figs")
def nine(system: System):
    st = float(system.stem["lc"])
    width = float(system.tokens.get("fig_width", 460.0))
    lsb = float(system.tokens.get("lsb_lc", 36.0))
    h = float(system.zones.cap) * 0.72
    cx = lsb + width / 2.0
    upper = bowl(
        system,
        cx=cx,
        cy=h * 0.68,
        rx=width * 0.40,
        ry=h * 0.28,
        thickness=st,
    )
    spine = open_bowl(
        system,
        cx=cx,
        cy=h * 0.40,
        rx=width * 0.40,
        ry=h * 0.40,
        thickness=st,
        open_side="left",
        aperture_deg=120.0,
        n=20,
    )
    return upper + spine
