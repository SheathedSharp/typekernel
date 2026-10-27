"""comma — period + short descending tail."""

from __future__ import annotations

from elements import diagonal_stroke, stem_rect

from typekernel.project import glyph
from typekernel.system import System


@glyph("comma", group="punct")
def comma(system: System):
    st = float(system.stem["lc"])
    size = st * 0.95
    lsb = float(system.tokens.get("lsb_lc", 40.0)) * 0.5
    dot = stem_rect(lsb, lsb + size, 0.0, size, prefix="dot")
    tail = diagonal_stroke(
        (lsb + size * 0.55, size * 0.35),
        (lsb + size * 0.15, -size * 0.85),
        weight=st * 0.55,
        tag_prefix="tail",
    )
    return dot + tail
