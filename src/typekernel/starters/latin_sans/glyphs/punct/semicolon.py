"""semicolon — colon with comma tail on lower dot."""

from __future__ import annotations

from elements import diagonal_stroke, stem_rect

from typekernel.project import glyph
from typekernel.system import System


@glyph("semicolon", group="punct")
def semicolon(system: System):
    st = float(system.stem["lc"])
    xh = float(system.zones.x)
    size = st * 0.9
    lsb = float(system.tokens.get("lsb_lc", 40.0)) * 0.5
    bot = stem_rect(lsb, lsb + size, 0.0, size, prefix="dot.bot")
    top = stem_rect(lsb, lsb + size, xh - size, xh, prefix="dot.top")
    tail = diagonal_stroke(
        (lsb + size * 0.55, size * 0.35),
        (lsb + size * 0.15, -size * 0.85),
        weight=st * 0.55,
        tag_prefix="tail",
    )
    return bot + top + tail
