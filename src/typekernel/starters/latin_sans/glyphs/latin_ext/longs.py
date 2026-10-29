"""longs — tall s without baseline finish . Signature-stable."""

from __future__ import annotations

from elements import WIDTHS, zone_anchors

from typekernel.anatomy import crossbar, stem
from typekernel.project import glyph
from typekernel.system import System


@glyph("longs", unicodes=(0x017F,), group="lc.mixed")
def longs(system: System):
    st = float(system.stem["lc"])
    thin = float(system.stem.get("lc_h", st * 0.85))
    asc = float(system.zones.asc)
    lsb = float(system.tokens.get("lsb_lc", 40.0))
    width = float(WIDTHS.get("f", 280))
    body = stem(lsb + width * 0.35, lsb + width * 0.35 + st, 0.0, asc * 0.92, name="stem")
    bar = crossbar(
        lsb + width * 0.35,
        lsb + width * 0.95,
        asc * 0.78,
        thick=thin,
        name="bar",
        ends="none",
    )
    return zone_anchors(body + bar, system, top="x")
