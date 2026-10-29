"""Figure eight — two stacked anatomy bowls ."""

from __future__ import annotations

from elements import WIDTHS

from typekernel.anatomy import bowl
from typekernel.project import glyph
from typekernel.system import System


@glyph("eight", group="figs")
def eight(system: System):
    st = float(system.stem["lc"])
    thin = float(system.stem.get("lc_h", st * 0.85))
    width = float(WIDTHS.get("fig", 500))
    lsb = float(system.tokens.get("lsb_lc", 40.0))
    h = float(system.zones.cap) * 0.72
    ov = float(system.overshoot.round) * 0.5
    exp = float(system.tokens.get("bowl_exponent", 2.15))
    cx = lsb + width / 2.0
    top = bowl(
        (cx, h * 0.70),
        width * 0.42,
        h * 0.28,
        thick=st,
        thin=thin,
        exponent=exp,
        overshoot=ov,
        name="bowl.t",
    )
    bot = bowl(
        (cx, h * 0.30),
        width * 0.46,
        h * 0.30,
        thick=st,
        thin=thin,
        exponent=exp,
        overshoot=ov,
        name="bowl.b",
    )
    return top + bot
