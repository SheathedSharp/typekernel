"""dotlessi — i without tittle (composite base)."""

from __future__ import annotations

from elements import WIDTHS, zone_anchors

from typekernel.anatomy import stem
from typekernel.project import glyph
from typekernel.system import System


@glyph("dotlessi", unicodes=(0x0131,), group="lc.straight")
def dotlessi(system: System):
    st = float(system.stem["lc"])
    xh = float(system.zones.x)
    width = float(WIDTHS["i"])
    lsb = float(system.tokens.get("lsb_lc", 40.0))
    x0 = lsb + (width - st) / 2.0
    body = stem(x0, x0 + st, 0.0, xh, name="stem")
    return zone_anchors(body, system, top="x", ogonek=True)
