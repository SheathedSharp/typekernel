"""endash — en-width mid bar."""

from __future__ import annotations

from elements import stem_rect

from typekernel.project import glyph
from typekernel.system import System


@glyph("endash", group="punct")
def endash(system: System):
    st = float(system.stem["lc"])
    xh = float(system.zones.x)
    lsb = float(system.tokens.get("lsb_lc", 40.0)) * 0.4
    length = float(system.tokens.get("n_width", 430)) * 0.55
    t = st * 0.85
    cy = xh * 0.48
    return stem_rect(lsb, lsb + length, cy - t / 2, cy + t / 2, prefix="bar")
