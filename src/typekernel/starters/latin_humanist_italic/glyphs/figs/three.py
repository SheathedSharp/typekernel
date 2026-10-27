"""Figure 3 — stacked left-open bowls overlapping at the waist."""

from __future__ import annotations

from elements import open_bowl

from typekernel.project import glyph
from typekernel.system import System


@glyph("three", group="figs")
def three(system: System):
    st = float(system.stem["lc"])
    width = float(system.tokens.get("fig_width", 460.0))
    lsb = float(system.tokens.get("lsb_lc", 36.0))
    h = float(system.zones.cap) * 0.72
    ov = float(system.overshoot.round) * 0.35
    cx = lsb + width * 0.52
    rx = width * 0.40
    overlap = st * 0.5
    ry_u = max(h * 0.24, (h * 0.55 + overlap) / 4.0)
    ry_l = max(h * 0.28, (h * 0.55 + overlap) / 4.0)
    upper = open_bowl(
        system,
        cx=cx,
        cy=h * 0.72,
        rx=rx * 0.92,
        ry=ry_u + ov,
        thickness=st,
        open_side="left",
        aperture_deg=90.0,
    )
    lower = open_bowl(
        system,
        cx=cx,
        cy=h * 0.28,
        rx=rx,
        ry=ry_l + ov,
        thickness=st,
        open_side="left",
        aperture_deg=90.0,
    )
    return upper + lower
