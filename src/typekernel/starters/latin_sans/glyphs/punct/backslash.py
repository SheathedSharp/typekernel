"""backslash — anatomy compensated diagonal (P3-7)."""

from __future__ import annotations

from elements import WIDTHS

from typekernel.draw import Writer, diagonal_band
from typekernel.project import glyph
from typekernel.system import System


@glyph("backslash", group="punct")
def backslash(system: System):
    st = float(system.stem["lc"])
    asc = float(system.zones.asc)
    desc = float(system.zones.desc)
    lsb = float(system.tokens.get("lsb_lc", 40.0)) * 0.4
    width = float(WIDTHS.get("slash", 320))
    left, right = diagonal_band(
        (lsb + st * 0.2, asc),
        (lsb + width - st * 0.2, desc),
        weight=st,
        compensate=True,
    )
    return (
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
