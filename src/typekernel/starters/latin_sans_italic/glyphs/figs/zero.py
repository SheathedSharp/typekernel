"""Figure 0 — elliptical bowl."""

from __future__ import annotations

from elements import WIDTHS, oval_points, stroke

from typekernel.project import glyph
from typekernel.system import System

_OVAL_N = 48


@glyph("zero", group="figs")
def zero(system: System):
    st = float(system.stem["lc"])
    width = float(WIDTHS.get("fig", 460.0))
    lsb = float(system.tokens["lsb_lc"])
    h = float(system.zones.cap) * 0.72
    ov = float(system.overshoot.round)
    return stroke(
        system,
        oval_points(lsb + width / 2.0, h / 2.0, width / 2.0 * 0.9, h / 2.0 + ov * 0.4, n=_OVAL_N),
        closed=True,
        thickness=st,
    )
