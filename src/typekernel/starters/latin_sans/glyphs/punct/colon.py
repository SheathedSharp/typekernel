"""colon — two dots."""

from __future__ import annotations

from elements import stem_rect

from typekernel.project import glyph
from typekernel.system import System


@glyph("colon", group="punct")
def colon(system: System):
    st = float(system.stem["lc"])
    xh = float(system.zones.x)
    size = st * 0.9
    lsb = float(system.tokens.get("lsb_lc", 40.0)) * 0.5
    bot = stem_rect(lsb, lsb + size, 0.0, size, prefix="dot.bot")
    top = stem_rect(lsb, lsb + size, xh - size, xh, prefix="dot.top")
    return bot + top
