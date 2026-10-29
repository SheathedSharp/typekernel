"""n-group glyph h — ascender stem + anatomy arch (P3-7)."""

from __future__ import annotations

from elements import WIDTHS, zone_anchors

from typekernel.anatomy import arch, stem
from typekernel.project import glyph
from typekernel.system import System


@glyph("h", group="lc.straight")
def h(system: System):
    st = float(system.stem["lc"])
    thin = float(system.stem.get("lc_h", st * 0.85))
    xh = float(system.zones.x)
    asc = float(system.zones.asc)
    width = float(WIDTHS.get("h", system.tokens["n_width"]))
    lsb = float(system.tokens.get("lsb_lc", 40.0))
    tension = float(system.tokens.get("shoulder_tension", 0.55))
    ov = float(system.overshoot.round)
    left = stem(lsb, lsb + st, 0.0, asc, name="stem.l")
    right = stem(lsb + width - st, lsb + width, 0.0, xh, name="stem.r")
    shoulder = arch(
        lsb + st,
        lsb + width - st,
        height=xh,
        thick=st,
        thin=thin,
        join_depth=st * 0.45,
        tension=tension,
        crown_shift=st * 0.15,
        overshoot=ov * 0.35,
        name="arch",
    )
    return zone_anchors(left + right + shoulder, system, top='x')
