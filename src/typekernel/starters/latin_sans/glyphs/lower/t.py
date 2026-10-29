"""Straight glyph t — stem to near-ascender + crossbar."""

from __future__ import annotations

from elements import WIDTHS, crossbar, stem_rect

from typekernel.project import glyph
from typekernel.system import System


@glyph("t", group="lc.straight")
def t(system: System):
    st = float(system.stem["lc"])
    xh = float(system.zones.x)
    asc = float(system.zones.asc)
    width = float(WIDTHS["t"])
    lsb = float(system.tokens.get("lsb_lc", 40.0))
    # Stem from baseline to a bit above x-height (not full ascender).
    top = xh + (asc - xh) * 0.55
    x0 = lsb + (width - st) / 2.0
    stem = stem_rect(x0, x0 + st, 0.0, top, prefix="stem")
    bar = crossbar(
        system,
        x0=lsb,
        x1=lsb + width,
        cy=xh,
        tag_prefix="t.bar",
    )
    return stem + bar
