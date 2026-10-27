"""Figure 2."""

from __future__ import annotations

import math

from elements import diagonal_stroke, stem_rect

from typekernel.plugins.passes.diagonal_comp import compensated_weight
from typekernel.project import glyph
from typekernel.system import System


@glyph("two", group="figs")
def two(system: System):
    st = float(system.stem["lc"])
    width = float(system.tokens.get("fig_width", 500))
    lsb = float(system.tokens.get("lsb_lc", 40.0))
    h = float(system.zones.cap) * 0.72
    top = stem_rect(lsb + width * 0.2, lsb + width, h - st, h, prefix="two.top")
    bot = stem_rect(lsb, lsb + width, 0.0, st, prefix="two.bot")
    ang = math.degrees(math.atan2(width * 0.65, h * 0.55))
    wt = compensated_weight(st, ang)
    diag = diagonal_stroke(
        (lsb + width - st * 0.3, h - st), (lsb + st * 0.4, st), weight=wt, tag_prefix="two.diag"
    )
    return top + diag + bot
