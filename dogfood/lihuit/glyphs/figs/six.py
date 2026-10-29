"""Figure six — anatomy bowl + stem (P3-7)."""

from __future__ import annotations

from elements import WIDTHS

from typekernel.anatomy import bowl, stem
from typekernel.project import glyph
from typekernel.system import System


@glyph("six", group="figs")
def six(system: System):
    st = float(system.stem["lc"])
    thin = float(system.stem.get("lc_h", st * 0.85))
    width = float(WIDTHS.get("fig", 500))
    lsb = float(system.tokens.get("lsb_lc", 40.0))
    h = float(system.zones.cap) * 0.72
    ov = float(system.overshoot.round) * 0.4
    exp = float(system.tokens.get("bowl_exponent", 2.15))
    ring = bowl(
        (lsb + width * 0.52, h * 0.35),
        width * 0.42,
        h * 0.32,
        thick=st,
        thin=thin,
        exponent=exp,
        overshoot=ov,
        name="bowl",
    )
    body = stem(lsb + st * 0.3, lsb + st * 1.3, h * 0.35, h, name="stem", foot="none")
    return ring + body
