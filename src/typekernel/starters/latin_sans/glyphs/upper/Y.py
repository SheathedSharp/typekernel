"""Diagonal glyph Y — anatomy diagonal_pair + stem (P3-7)."""

from __future__ import annotations

from elements import WIDTHS

from typekernel.anatomy import diagonal_pair, stem
from typekernel.project import glyph
from typekernel.system import System


@glyph("Y", group="uc.diagonal")
def glyph_Y(system: System):
    st = float(system.stem["uc"])
    cap = float(system.zones.cap)
    width = float(WIDTHS["Y"])
    lsb = float(system.tokens.get("lsb_uc", 50.0))
    join_y = cap * 0.45
    cx = lsb + width / 2.0
    arms = diagonal_pair(
        (cx, join_y),
        (lsb + st * 0.3, cap),
        (lsb + width - st * 0.3, cap),
        weight=st,
        name="diag",
    )
    body = stem(cx - st / 2.0, cx + st / 2.0, 0.0, join_y + st * 0.35, name="stem")
    return arms + body
