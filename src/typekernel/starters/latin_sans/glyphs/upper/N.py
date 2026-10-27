"""Rest glyph N — two stems + diagonal."""

from __future__ import annotations

import math

from elements import diagonal_stroke, stem_rect

from typekernel.plugins.passes.diagonal_comp import compensated_weight
from typekernel.project import glyph
from typekernel.system import System


@glyph("N", group="uc.diagonal")
def glyph_N(system: System):
    st = float(system.stem["uc"])
    cap = float(system.zones.cap)
    width = float(system.tokens["N_width"])
    lsb = float(system.tokens.get("lsb_uc", 50.0))
    left = stem_rect(lsb, lsb + st, 0.0, cap, prefix="stem.l")
    right = stem_rect(lsb + width - st, lsb + width, 0.0, cap, prefix="stem.r")
    ang = math.degrees(math.atan2(width - 2 * st, cap))
    wt = compensated_weight(st, ang)
    diag = diagonal_stroke(
        (lsb + st * 0.5, cap),
        (lsb + width - st * 0.5, 0.0),
        weight=wt,
        tag_prefix="N.diag",
    )
    return left + right + diag
