"""Diagonal glyph Z — bars + diagonal."""

from __future__ import annotations

import math

from elements import WIDTHS, diagonal_stroke, stem_rect

from typekernel.plugins.passes.diagonal_comp import compensated_weight
from typekernel.project import glyph
from typekernel.system import System


@glyph("Z", group="uc.diagonal")
def glyph_Z(system: System):
    st = float(system.stem["uc"])
    cap = float(system.zones.cap)
    width = float(WIDTHS["Z"])
    lsb = float(system.tokens.get("lsb_uc", 50.0))
    bar = float(system.stem.get("uc_h", st * 0.85))
    top = stem_rect(lsb, lsb + width, cap - bar, cap, prefix="Z.top")
    bot = stem_rect(lsb, lsb + width, 0.0, bar, prefix="Z.bot")
    ang = math.degrees(math.atan2(width - st, cap - 2 * bar))
    wt = compensated_weight(st, ang)
    diag = diagonal_stroke(
        (lsb + width - bar * 0.4, cap - bar),
        (lsb + bar * 0.4, bar),
        weight=wt,
        tag_prefix="Z.diag",
    )
    return top + bot + diag
