"""Mixed glyph K — anatomy stem + diagonal arms (P3-7)."""

from __future__ import annotations

from elements import WIDTHS

from typekernel.anatomy import stem
from typekernel.draw import Writer, diagonal_band
from typekernel.project import glyph
from typekernel.system import System


def _arm(p_top, p_bottom, *, weight: float, name: str):
    left, right = diagonal_band(p_top, p_bottom, weight=weight, compensate=True)
    return (
        Writer()
        .start(left.start)
        .corner(f"{name}.top.l")
        .fragment(left)
        .corner(f"{name}.foot.l")
        .line(right.start)
        .corner(f"{name}.foot.r")
        .fragment(right)
        .corner(f"{name}.top.r")
        .line(left.start)
        .close()
        .build()
    )


@glyph("K", group="uc.mixed")
def glyph_K(system: System):
    st = float(system.stem["uc"])
    cap = float(system.zones.cap)
    width = float(WIDTHS["K"])
    lsb = float(system.tokens.get("lsb_uc", 50.0))
    body = stem(lsb, lsb + st, 0.0, cap, name="stem.l")
    join_y = cap * 0.48
    join_x = lsb + st * 0.7
    tip_x = lsb + width - st * 0.2
    upper = _arm((tip_x, cap), (join_x, join_y), weight=st, name="diag.t")
    lower = _arm((join_x, join_y), (tip_x, 0.0), weight=st, name="diag.b")
    return body + upper + lower
