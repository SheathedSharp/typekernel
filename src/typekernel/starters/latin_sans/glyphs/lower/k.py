"""Mixed glyph k — anatomy stem + diagonal arms (P3-7)."""

from __future__ import annotations

from elements import WIDTHS, zone_anchors

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


@glyph("k", group="lc.mixed")
def k(system: System):
    st = float(system.stem["lc"])
    xh = float(system.zones.x)
    width = float(WIDTHS["k"])
    lsb = float(system.tokens.get("lsb_lc", 40.0))
    body = stem(lsb, lsb + st, 0.0, xh, name="stem.l")
    join_y = xh * 0.48
    join_x = lsb + st * 0.65
    tip_x = lsb + width - st * 0.25
    upper = _arm((tip_x, xh), (join_x, join_y), weight=st, name="diag.t")
    lower = _arm((join_x, join_y), (tip_x, 0.0), weight=st, name="diag.b")
    return zone_anchors(body + upper + lower, system, top='x')
