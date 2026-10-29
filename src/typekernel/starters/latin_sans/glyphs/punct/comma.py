"""comma — anatomy dot + diagonal tail ."""

from __future__ import annotations

from typekernel.anatomy import dot
from typekernel.draw import Writer, diagonal_band
from typekernel.project import glyph
from typekernel.system import System


@glyph("comma", group="punct")
def comma(system: System):
    st = float(system.stem["lc"])
    size = st * 0.95
    lsb = float(system.tokens.get("lsb_lc", 40.0)) * 0.5
    head = dot((lsb + size / 2.0, size / 2.0), size, shape="square", name="dot")
    left, right = diagonal_band(
        (lsb + size * 0.55, size * 0.35),
        (lsb + size * 0.15, -size * 0.85),
        weight=st * 0.55,
        compensate=True,
    )
    tail = (
        Writer()
        .start(left.start)
        .corner("tail.top.l")
        .fragment(left)
        .corner("tail.foot.l")
        .line(right.start)
        .corner("tail.foot.r")
        .fragment(right)
        .corner("tail.top.r")
        .line(left.start)
        .close()
        .build()
    )
    return head + tail
