"""Mixed glyph P — anatomy stem + upper bowl (P3-7)."""

from __future__ import annotations

from elements import WIDTHS

from typekernel.anatomy import bowl, stem
from typekernel.project import glyph
from typekernel.system import System


@glyph("P", group="uc.mixed")
def glyph_P(system: System):
    st = float(system.stem["uc"])
    thin = float(system.stem.get("uc_h", st * 0.85))
    cap = float(system.zones.cap)
    width = float(WIDTHS["P"])
    lsb = float(system.tokens.get("lsb_uc", 50.0))
    ov = float(system.overshoot.round) * 0.4
    exp = float(system.tokens.get("bowl_exponent", 2.15))
    left = stem(lsb, lsb + st, 0.0, cap, name="stem.l")
    cx = lsb + st + (width - st) * 0.48
    ring = bowl(
        (cx, cap * 0.70),
        (width - st) * 0.50,
        cap * 0.30,
        thick=st,
        thin=thin,
        exponent=exp,
        overshoot=ov,
        name="bowl",
    )
    return left + ring
