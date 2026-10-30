"""Mixed glyph B — anatomy stem + two bowls ."""

from __future__ import annotations

from elements import WIDTHS, zone_anchors

from typekernel.anatomy import bowl, stem
from typekernel.project import glyph
from typekernel.system import System


@glyph("B", group="uc.mixed")
def glyph_B(system: System):
    st = float(system.stem["uc"])
    thin = float(system.stem.get("uc_h", st * 0.85))
    cap = float(system.zones.cap)
    width = float(WIDTHS["B"])
    lsb = float(system.tokens.get("lsb_uc", 50.0))
    ov = float(system.overshoot.round) * 0.4
    exp = float(system.tokens.get("bowl_exponent", 2.15))
    left = stem(lsb, lsb + st, 0.0, cap, name="stem.l")
    # Pull bowls into the stem and let them meet at the waist (2 counters).
    cx = lsb + st + (width - st) * 0.40
    top = bowl(
        (cx, cap * 0.70),
        (width - st) * 0.52,
        cap * 0.27,
        thick=st,
        thin=thin,
        exponent=exp,
        overshoot=ov,
        name="bowl.t",
    )
    bot = bowl(
        (cx + st * 0.05, cap * 0.32),
        (width - st) * 0.56,
        cap * 0.29,
        thick=st,
        thin=thin,
        exponent=exp,
        overshoot=ov,
        name="bowl.b",
    )
    return zone_anchors(left + top + bot, system, top='cap')
