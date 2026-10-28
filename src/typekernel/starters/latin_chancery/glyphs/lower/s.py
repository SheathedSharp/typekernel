"""Lowercase s — stacked open bowls."""
from __future__ import annotations

from elements import open_bowl

from typekernel.project import glyph
from typekernel.system import System


@glyph("s", group="lc.round")
def s(system: System):
    st = float(system.stem["lc"])
    xh = float(system.zones.x)
    width = float(system.tokens.get("s_width", 340.0))
    lsb = float(system.tokens.get("lsb_lc", 32.0))
    ov = float(system.overshoot.round)
    cx = lsb + width / 2.0
    rx = width / 2.0 * 0.98
    overlap = st * 0.85
    ry = max(xh * 0.32, (xh + 2.0 * ov + overlap) / 4.0)
    upper = open_bowl(
        system, cx=cx, cy=(xh + ov) - ry, rx=rx, ry=ry, thickness=st,
        open_side="right", aperture_deg=72.0,
    )
    lower = open_bowl(
        system, cx=cx, cy=(-ov) + ry, rx=rx, ry=ry, thickness=st,
        open_side="left", aperture_deg=72.0,
    )
    return upper + lower
