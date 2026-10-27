"""Figure 0 — elliptical bowl (shared bowl element)."""

from __future__ import annotations

from elements import bowl

from typekernel.project import glyph
from typekernel.system import System


@glyph("zero", group="figs")
def zero(system: System):
    st = float(system.stem["lc"])
    width = float(system.tokens.get("fig_width", 460.0))
    lsb = float(system.tokens.get("lsb_lc", 36.0))
    h = float(system.zones.cap) * 0.72
    ov = float(system.overshoot.round)
    return bowl(
        system,
        cx=lsb + width / 2.0,
        cy=h / 2.0,
        rx=width / 2.0 * 0.9,
        ry=h / 2.0 + ov * 0.4,
        thickness=st,
    )
