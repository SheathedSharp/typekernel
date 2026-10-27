"""Figure 6 — bowl with overlapping upper open spine."""

from __future__ import annotations

from elements import bowl, open_bowl

from typekernel.project import glyph
from typekernel.system import System


@glyph("six", group="figs")
def six(system: System):
    st = float(system.stem["lc"])
    width = float(system.tokens.get("fig_width", 460.0))
    lsb = float(system.tokens.get("lsb_lc", 36.0))
    h = float(system.zones.cap) * 0.72
    cx = lsb + width / 2.0
    lower = bowl(
        system,
        cx=cx,
        cy=h * 0.32,
        rx=width * 0.40,
        ry=h * 0.30,
        thickness=st,
    )
    # Open bowl covering the upper left/top so it merges into the lower ring.
    spine = open_bowl(
        system,
        cx=cx,
        cy=h * 0.55,
        rx=width * 0.40,
        ry=h * 0.40,
        thickness=st,
        open_side="right",
        aperture_deg=120.0,
        n=20,
    )
    return lower + spine
