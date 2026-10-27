"""question — top bar + stem stub + baseline dot."""

from __future__ import annotations

from elements import stem_rect

from typekernel.project import glyph
from typekernel.system import System


@glyph("question", group="punct")
def question(system: System):
    st = float(system.stem["lc"])
    xh = float(system.zones.x)
    size = st * 0.95
    lsb = float(system.tokens.get("lsb_lc", 40.0)) * 0.4
    width = float(system.tokens.get("question_width", 320))
    top = stem_rect(lsb + width * 0.15, lsb + width, xh - st, xh, prefix="q.top")
    stem = stem_rect(
        lsb + width - st * 1.1,
        lsb + width - st * 0.1,
        xh * 0.42,
        xh - st * 0.5,
        prefix="q.stem",
    )
    stub = stem_rect(
        lsb + width * 0.42,
        lsb + width * 0.42 + st,
        xh * 0.38,
        xh * 0.55,
        prefix="q.stub",
    )
    dot = stem_rect(
        lsb + width * 0.42, lsb + width * 0.42 + size, 0.0, size, prefix="dot"
    )
    return top + stem + stub + dot
