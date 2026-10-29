"""Rest glyph S — capital stacked open_bowl pair (same element as s)."""

from __future__ import annotations

from elements import WIDTHS, open_bowl

from typekernel.project import glyph
from typekernel.system import System


@glyph("S", group="uc.round")
def glyph_S(system: System):
    st = float(system.stem["uc"])
    cap = float(system.zones.cap)
    width = float(WIDTHS["S"])
    lsb = float(system.tokens.get("lsb_uc", 50.0))
    ov = float(system.overshoot.round)
    cx = lsb + width / 2.0
    rx = width / 2.0 * 0.95
    overlap = st * 0.55
    ry = max(cap * 0.30, (cap + 2.0 * ov + overlap) / 4.0)
    upper = open_bowl(
        system,
        cx=cx,
        cy=(cap + ov) - ry,
        rx=rx,
        ry=ry,
        thickness=st,
        open_side="right",
        tag_prefix="S.upper",
    )
    lower = open_bowl(
        system,
        cx=cx,
        cy=(-ov) + ry,
        rx=rx,
        ry=ry,
        thickness=st,
        open_side="left",
        tag_prefix="S.lower",
    )
    return upper + lower
