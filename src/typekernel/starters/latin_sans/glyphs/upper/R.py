"""Rest glyph R — P + diagonal leg."""

from __future__ import annotations

import math

from elements import bowl, diagonal_stroke, stem_rect

from typekernel.plugins.passes.diagonal_comp import compensated_weight
from typekernel.project import glyph
from typekernel.system import System


@glyph("R", group="uc.bowl")
def glyph_R(system: System):
    st = float(system.stem["uc"])
    cap = float(system.zones.cap)
    width = float(system.tokens["R_width"])
    lsb = float(system.tokens.get("lsb_uc", 50.0))
    ov = float(system.overshoot.round) * 0.4
    stem = stem_rect(lsb, lsb + st, 0.0, cap, prefix="stem.l")
    cx = lsb + st + (width - st) * 0.45
    bowl_ = bowl(
        system,
        cx=cx,
        cy=cap * 0.70,
        rx=(width - st) * 0.48,
        ry=cap * 0.30 + ov,
        thickness=st,
    )
    join_y = cap * 0.42
    ang = math.degrees(math.atan2(width * 0.45, join_y))
    wt = compensated_weight(st, ang)
    leg = diagonal_stroke(
        (lsb + st * 0.7, join_y),
        (lsb + width - st * 0.2, 0.0),
        weight=wt,
        tag_prefix="R.leg",
    )
    return stem + bowl_ + leg
