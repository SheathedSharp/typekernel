"""Figure four — anatomy stem + bar + diagonal ."""

from __future__ import annotations

from elements import WIDTHS

from typekernel.anatomy import crossbar, stem
from typekernel.draw import Writer, diagonal_band
from typekernel.project import glyph
from typekernel.system import System


@glyph("four", group="figs")
def four(system: System):
    st = float(system.stem["lc"])
    thin = float(system.stem.get("lc_h", st * 0.85))
    width = float(WIDTHS.get("fig", 500))
    lsb = float(system.tokens.get("lsb_lc", 40.0))
    h = float(system.zones.cap) * 0.72
    x_stem = lsb + width * 0.62
    body = stem(x_stem, x_stem + st, 0.0, h, name="stem")
    bar = crossbar(lsb, lsb + width, h * 0.38, thick=thin, name="bar", ends="none")
    left, right = diagonal_band(
        (lsb + st * 0.3, h), (x_stem + st * 0.5, h * 0.38), weight=st, compensate=True
    )
    diag = (
        Writer()
        .start(left.start)
        .corner("diag.top.l")
        .fragment(left)
        .corner("diag.foot.l")
        .line(right.start)
        .corner("diag.foot.r")
        .fragment(right)
        .corner("diag.top.r")
        .line(left.start)
        .close()
        .build()
    )
    return body + bar + diag
