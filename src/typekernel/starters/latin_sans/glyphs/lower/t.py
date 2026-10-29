"""Mixed glyph t — anatomy stem + crossbar (P3-7)."""

from __future__ import annotations

from elements import WIDTHS, zone_anchors

from typekernel.anatomy import crossbar, stem
from typekernel.project import glyph
from typekernel.system import System


@glyph("t", group="lc.mixed")
def t(system: System):
    st = float(system.stem["lc"])
    thin = float(system.stem.get("lc_h", st * 0.85))
    xh = float(system.zones.x)
    asc = float(system.zones.asc)
    width = float(WIDTHS["t"])
    lsb = float(system.tokens.get("lsb_lc", 40.0))
    top = xh + (asc - xh) * 0.55
    x0 = lsb + (width - st) / 2.0
    body = stem(x0, x0 + st, 0.0, top, name="stem")
    bar = crossbar(
        lsb,
        lsb + width,
        xh,
        thick=thin,
        name="bar",
        ends="none",
    )
    return zone_anchors(body + bar, system, top='x')
