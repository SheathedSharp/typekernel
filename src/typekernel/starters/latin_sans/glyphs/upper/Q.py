"""O-group glyph Q — O with diagonal tail."""

from __future__ import annotations

import math

from elements import bowl, diagonal_stroke

from typekernel.plugins.passes.diagonal_comp import compensated_weight
from typekernel.project import glyph
from typekernel.system import System


@glyph("Q", group="uc.bowl")
def glyph_Q(system: System):
    st = float(system.stem["uc"])
    cap = float(system.zones.cap)
    width = float(system.tokens["Q_width"])
    lsb = float(system.tokens.get("lsb_uc", 50.0))
    ov = float(system.overshoot.round)
    cx = lsb + width / 2.0
    cy = cap / 2.0
    rx, ry = width / 2.0, cap / 2.0 + ov
    ring = bowl(system, cx=cx, cy=cy, rx=rx, ry=ry, thickness=st)
    # Tail from lower-right of bowl toward bottom-right.
    ang = math.degrees(math.atan2(width * 0.28, cap * 0.28))
    wt = compensated_weight(st, ang)
    tail = diagonal_stroke(
        (cx + rx * 0.25, cy - ry * 0.35),
        (lsb + width - st * 0.2, -ov * 0.5),
        weight=wt,
        tag_prefix="Q.tail",
    )
    return ring + tail
