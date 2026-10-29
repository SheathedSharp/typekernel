"""Figure nine — anatomy bowl + stem (P3-7)."""

from __future__ import annotations

from elements import WIDTHS

from typekernel.anatomy import bowl, stem
from typekernel.project import glyph
from typekernel.system import System


@glyph("nine", group="figs")
def nine(system: System):
    st = float(system.stem["lc"])
    thin = float(system.stem.get("lc_h", st * 0.85))
    width = float(WIDTHS.get("fig", 500))
    lsb = float(system.tokens.get("lsb_lc", 40.0))
    h = float(system.zones.cap) * 0.72
    ov = float(system.overshoot.round) * 0.4
    exp = float(system.tokens.get("bowl_exponent", 2.15))
    ring = bowl(
        (lsb + width * 0.48, h * 0.62),
        width * 0.42,
        h * 0.30,
        thick=st,
        thin=thin,
        exponent=exp,
        overshoot=ov,
        name="bowl",
    )
    body = stem(
        lsb + width - st * 1.3,
        lsb + width - st * 0.3,
        0.0,
        h * 0.62,
        name="stem",
        top="none",
    )
    return ring + body
