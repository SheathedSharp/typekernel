"""n-group glyph r — stem + short anatomy arch stub ."""

from __future__ import annotations

from elements import WIDTHS, zone_anchors

from typekernel.anatomy import arch, stem
from typekernel.project import glyph
from typekernel.system import System


@glyph("r", group="lc.straight")
def r(system: System):
    st = float(system.stem["lc"])
    thin = float(system.stem.get("lc_h", st * 0.85))
    xh = float(system.zones.x)
    width = float(WIDTHS["r"])
    lsb = float(system.tokens.get("lsb_lc", 40.0))
    tension = float(system.tokens.get("shoulder_tension", 0.55))
    ov = float(system.overshoot.round)
    body = stem(lsb, lsb + st, 0.0, xh, name="stem.l")
    shoulder = arch(
        lsb + st * 0.85,
        lsb + width,
        height=xh,
        thick=st * 0.9,
        thin=thin * 0.9,
        join_depth=st * 0.35,
        tension=tension,
        overshoot=ov * 0.25,
        name="arch",
    )
    return zone_anchors(body + shoulder, system, top='x')
