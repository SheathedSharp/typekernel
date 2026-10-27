"""Round glyph s — stacked open_bowl pair overlapping at the waist."""

from __future__ import annotations

from elements import open_bowl

from typekernel.project import glyph
from typekernel.system import System


@glyph("s", group="lc.round")
def s(system: System):
    st = float(system.stem["lc"])
    xh = float(system.zones.x)
    width = float(system.tokens["s_width"])
    lsb = float(system.tokens.get("lsb_lc", 40.0))
    ov = float(system.overshoot.round)
    cx = lsb + width / 2.0
    rx = width / 2.0 * 0.95
    # Fit within [-ov, xh+ov]; choose ry so south/north strokes overlap.
    overlap = st * 0.55
    ry = max(xh * 0.30, (xh + 2.0 * ov + overlap) / 4.0)
    upper = open_bowl(
        system,
        cx=cx,
        cy=(xh + ov) - ry,
        rx=rx,
        ry=ry,
        thickness=st,
        open_side="right",
        tag_prefix="s.upper",
    )
    lower = open_bowl(
        system,
        cx=cx,
        cy=(-ov) + ry,
        rx=rx,
        ry=ry,
        thickness=st,
        open_side="left",
        tag_prefix="s.lower",
    )
    return upper + lower
