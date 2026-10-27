"""Rest glyph P — stem + upper bowl."""

from __future__ import annotations

from elements import bowl, stem_rect

from typekernel.project import glyph
from typekernel.system import System


@glyph("P", group="uc.bowl")
def glyph_P(system: System):
    st = float(system.stem["uc"])
    cap = float(system.zones.cap)
    width = float(system.tokens["P_width"])
    lsb = float(system.tokens.get("lsb_uc", 50.0))
    ov = float(system.overshoot.round) * 0.4
    stem = stem_rect(lsb, lsb + st, 0.0, cap, prefix="stem.l")
    cx = lsb + st + (width - st) * 0.48
    bowl_ = bowl(
        system,
        cx=cx,
        cy=cap * 0.70,
        rx=(width - st) * 0.50,
        ry=cap * 0.30 + ov,
        thickness=st,
    )
    return stem + bowl_
