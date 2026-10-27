"""Figure 8 — two stacked bowls (shared bowl element)."""

from __future__ import annotations

from elements import bowl

from typekernel.project import glyph
from typekernel.system import System


@glyph("eight", group="figs")
def eight(system: System):
    st = float(system.stem["lc"])
    width = float(system.tokens.get("fig_width", 460.0))
    lsb = float(system.tokens.get("lsb_lc", 36.0))
    h = float(system.zones.cap) * 0.72
    ov = float(system.overshoot.round) * 0.5
    cx = lsb + width / 2.0
    # Larger rings + intentional waist overlap so stroke reads near o-weight.
    top = bowl(
        system,
        cx=cx,
        cy=h * 0.70,
        rx=width * 0.42,
        ry=h * 0.28 + ov,
        thickness=st,
    )
    bot = bowl(
        system,
        cx=cx,
        cy=h * 0.30,
        rx=width * 0.46,
        ry=h * 0.30 + ov,
        thickness=st,
    )
    return top + bot
