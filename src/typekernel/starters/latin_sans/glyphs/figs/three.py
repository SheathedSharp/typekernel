"""Figure three — stacked anatomy open_bowls (open counter)."""

from __future__ import annotations

from elements import WIDTHS

from typekernel.anatomy import open_bowl
from typekernel.project import glyph
from typekernel.system import System


@glyph("three", group="figs")
def three(system: System):
    st = float(system.stem["lc"])
    thin = float(system.stem.get("lc_h", st * 0.85))
    width = float(WIDTHS.get("fig", 500))
    lsb = float(system.tokens.get("lsb_lc", 40.0))
    h = float(system.zones.cap) * 0.72
    ov = float(system.overshoot.round) * 0.4
    exp = float(system.tokens.get("bowl_exponent", 2.15))
    aperture = float(system.tokens.get("bowl_aperture", 0.42))
    tension = float(system.tokens.get("shoulder_tension", 0.55))
    cx = lsb + width * 0.55
    top = open_bowl(
        (cx, h * 0.70),
        width * 0.40,
        h * 0.26,
        thick=st,
        thin=thin,
        aperture=aperture,
        open_side="left",
        exponent=exp,
        overshoot=ov,
        tension=tension,
        name="bowl.t",
        aperture_index=0,
    )
    bot = open_bowl(
        (cx, h * 0.30),
        width * 0.42,
        h * 0.28,
        thick=st,
        thin=thin,
        aperture=aperture,
        open_side="left",
        exponent=exp,
        overshoot=ov,
        tension=tension,
        name="bowl.b",
        aperture_index=1,
    )
    return top + bot
