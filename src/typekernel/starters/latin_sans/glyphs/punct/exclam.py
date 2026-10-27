"""exclam — stem + baseline dot."""

from __future__ import annotations

from elements import stem_rect

from typekernel.project import glyph
from typekernel.system import System


@glyph("exclam", group="punct")
def exclam(system: System):
    st = float(system.stem["lc"])
    xh = float(system.zones.x)
    size = st * 0.95
    lsb = float(system.tokens.get("lsb_lc", 40.0)) * 0.55
    x0 = lsb + (size - st) / 2.0
    stem = stem_rect(x0, x0 + st, size * 1.35, xh, prefix="stem")
    dot = stem_rect(lsb, lsb + size, 0.0, size, prefix="dot")
    return stem + dot
