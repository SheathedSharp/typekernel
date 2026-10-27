"""Figure 4 — open triangle + stem."""

from __future__ import annotations

import math

from elements import crossbar, diagonal_stroke, stem_rect

from typekernel.plugins.passes.diagonal_comp import compensated_weight
from typekernel.project import glyph
from typekernel.system import System


@glyph("four", group="figs")
def four(system: System):
    st = float(system.stem["lc"])
    width = float(system.tokens.get("fig_width", 500))
    lsb = float(system.tokens.get("lsb_lc", 40.0))
    h = float(system.zones.cap) * 0.72
    x_stem = lsb + width * 0.62
    stem = stem_rect(x_stem, x_stem + st, 0.0, h, prefix="stem")
    bar = crossbar(system, x0=lsb, x1=lsb + width, cy=h * 0.38, tag_prefix="four.bar")
    ang = math.degrees(math.atan2(width * 0.5, h * 0.55))
    wt = compensated_weight(st, ang)
    diag = diagonal_stroke(
        (lsb + st * 0.3, h), (x_stem + st * 0.5, h * 0.38), weight=wt, tag_prefix="four.diag"
    )
    return stem + bar + diag
