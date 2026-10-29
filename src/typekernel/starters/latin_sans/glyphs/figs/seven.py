"""Figure 7 — top bar + diagonal."""

from __future__ import annotations

import math

from elements import WIDTHS, diagonal_stroke, stem_rect

from typekernel.plugins.passes.diagonal_comp import compensated_weight
from typekernel.project import glyph
from typekernel.system import System


@glyph("seven", group="figs")
def seven(system: System):
    st = float(system.stem["lc"])
    width = float(WIDTHS.get("fig", 500))
    lsb = float(system.tokens.get("lsb_lc", 40.0))
    h = float(system.zones.cap) * 0.72
    top = stem_rect(lsb, lsb + width, h - st, h, prefix="seven.top")
    ang = math.degrees(math.atan2(width * 0.55, h * 0.85))
    wt = compensated_weight(st, ang)
    diag = diagonal_stroke(
        (lsb + width - st * 0.3, h - st), (lsb + width * 0.35, 0.0), weight=wt, tag_prefix="seven.diag"
    )
    return top + diag
