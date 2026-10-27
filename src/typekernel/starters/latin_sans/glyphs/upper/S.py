"""Rest glyph S — capital stacked open_bowl pair (same element as s)."""

from __future__ import annotations

from elements import open_bowl

from typekernel.project import glyph
from typekernel.system import System


@glyph("S", group="uc.round")
def glyph_S(system: System):
    st = float(system.stem["uc"])
    cap = float(system.zones.cap)
    width = float(system.tokens["S_width"])
    lsb = float(system.tokens.get("lsb_uc", 50.0))
    ov = float(system.overshoot.round)
    cx = lsb + width / 2.0
    rx = width / 2.0 * 0.95
    ry = cap * 0.36 + ov * 0.3
    mid = cap / 2.0
    overlap = st * 0.55
    upper = open_bowl(
        system,
        cx=cx,
        cy=mid + ry - overlap,
        rx=rx,
        ry=ry,
        thickness=st,
        open_side="right",
        tag_prefix="S.upper",
    )
    lower = open_bowl(
        system,
        cx=cx,
        cy=mid - ry + overlap,
        rx=rx,
        ry=ry,
        thickness=st,
        open_side="left",
        tag_prefix="S.lower",
    )
    return upper + lower
