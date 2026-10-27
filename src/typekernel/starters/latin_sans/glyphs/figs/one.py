"""Figure 1 — stem with top flag."""

from __future__ import annotations

from elements import diagonal_stroke, stem_rect

from typekernel.project import glyph
from typekernel.system import System


@glyph("one", group="figs")
def one(system: System):
    st = float(system.stem["lc"])
    width = float(system.tokens.get("fig_width", 500))
    lsb = float(system.tokens.get("lsb_lc", 40.0))
    h = float(system.zones.cap) * 0.72
    x0 = lsb + (width - st) / 2.0
    stem = stem_rect(x0, x0 + st, 0.0, h, prefix="stem")
    flag = diagonal_stroke(
        (x0 - st * 0.8, h * 0.72), (x0 + st * 0.5, h), weight=st * 0.85, tag_prefix="flag"
    )
    return stem + flag
