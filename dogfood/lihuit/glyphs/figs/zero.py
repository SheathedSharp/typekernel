"""Figure zero — anatomy bowl (P3-7)."""

from __future__ import annotations

from elements import WIDTHS

from typekernel.anatomy import bowl
from typekernel.project import glyph
from typekernel.system import System


@glyph("zero", group="figs")
def zero(system: System):
    st = float(system.stem["lc"])
    thin = float(system.stem.get("lc_h", st * 0.85))
    width = float(WIDTHS.get("fig", 500))
    lsb = float(system.tokens.get("lsb_lc", 40.0))
    h = float(system.zones.cap) * 0.72
    ov = float(system.overshoot.round)
    exp = float(system.tokens.get("bowl_exponent", 2.15))
    return bowl(
        (lsb + width / 2.0, h / 2.0),
        width / 2.0 * 0.92,
        h / 2.0,
        thick=st,
        thin=thin,
        exponent=exp,
        overshoot=ov,
        name="bowl",
    )
