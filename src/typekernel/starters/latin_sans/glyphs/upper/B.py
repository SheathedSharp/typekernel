"""Rest glyph B — stem + two bowls."""

from __future__ import annotations

from elements import WIDTHS, bowl, stem_rect

from typekernel.project import glyph
from typekernel.system import System


@glyph("B", group="uc.bowl")
def glyph_B(system: System):
    st = float(system.stem["uc"])
    cap = float(system.zones.cap)
    width = float(WIDTHS["B"])
    lsb = float(system.tokens.get("lsb_uc", 50.0))
    ov = float(system.overshoot.round) * 0.4
    stem = stem_rect(lsb, lsb + st, 0.0, cap, prefix="stem.l")
    # Upper bowl (slightly narrower), lower bowl.
    cx = lsb + st + (width - st) * 0.48
    top = bowl(
        system,
        cx=cx,
        cy=cap * 0.72,
        rx=(width - st) * 0.48,
        ry=cap * 0.28 + ov,
        thickness=st,
    )
    bot = bowl(
        system,
        cx=cx + st * 0.05,
        cy=cap * 0.30,
        rx=(width - st) * 0.52,
        ry=cap * 0.30 + ov,
        thickness=st,
    )
    return stem + top + bot
