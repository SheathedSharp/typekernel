"""semicolon — anatomy dots + tail (P3-7)."""

from __future__ import annotations

from typekernel.anatomy import dot
from typekernel.draw import Writer, diagonal_band
from typekernel.project import glyph
from typekernel.system import System


@glyph("semicolon", group="punct")
def semicolon(system: System):
    st = float(system.stem["lc"])
    xh = float(system.zones.x)
    size = st * 0.9
    lsb = float(system.tokens.get("lsb_lc", 40.0)) * 0.5
    cx = lsb + size / 2.0
    bot = dot((cx, size / 2.0), size, shape="square", name="dot.b")
    top = dot((cx, xh - size / 2.0), size, shape="square", name="dot.t")
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
    return bot + top + tail
