"""Figure one — anatomy stem + flag band (P3-7)."""

from __future__ import annotations

from elements import WIDTHS

from typekernel.anatomy import stem
from typekernel.draw import Writer, diagonal_band
from typekernel.project import glyph
from typekernel.system import System


@glyph("one", group="figs")
def one(system: System):
    st = float(system.stem["lc"])
    width = float(WIDTHS.get("fig", 500))
    lsb = float(system.tokens.get("lsb_lc", 40.0))
    h = float(system.zones.cap) * 0.72
    x0 = lsb + (width - st) / 2.0
    body = stem(x0, x0 + st, 0.0, h, name="stem")
    left, right = diagonal_band(
        (x0 - st * 0.8, h * 0.72), (x0 + st * 0.5, h), weight=st * 0.85, compensate=True
    )
    flag = (
        Writer()
        .start(left.start)
        .corner("spur.top.l")
        .fragment(left)
        .corner("spur.foot.l")
        .line(right.start)
        .corner("spur.foot.r")
        .fragment(right)
        .corner("spur.top.r")
        .line(left.start)
        .close()
        .build()
    )
    return body + flag
