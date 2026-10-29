"""Figure five — anatomy bar + stub + open_bowl (open counter)."""

from __future__ import annotations

from elements import WIDTHS

from typekernel.anatomy import crossbar, open_bowl, stem
from typekernel.project import glyph
from typekernel.system import System


@glyph("five", group="figs")
def five(system: System):
    st = float(system.stem["lc"])
    thin = float(system.stem.get("lc_h", st * 0.85))
    width = float(WIDTHS.get("fig", 500))
    lsb = float(system.tokens.get("lsb_lc", 40.0))
    h = float(system.zones.cap) * 0.72
    ov = float(system.overshoot.round) * 0.4
    exp = float(system.tokens.get("bowl_exponent", 2.15))
    aperture = float(system.tokens.get("bowl_aperture", 0.42))
    tension = float(system.tokens.get("shoulder_tension", 0.55))
    top = crossbar(
        lsb, lsb + width * 0.85, h - thin / 2.0, thick=thin, name="bar", ends="none"
    )
    stub = stem(lsb, lsb + st, h * 0.42, h - thin * 0.5, name="stem", top="none")
    bowl_ = open_bowl(
        (lsb + width * 0.55, h * 0.32),
        width * 0.42,
        h * 0.30,
        thick=st,
        thin=thin,
        aperture=aperture,
        open_side="left",
        exponent=exp,
        overshoot=ov,
        tension=tension,
        name="bowl",
    )
    return top + stub + bowl_
