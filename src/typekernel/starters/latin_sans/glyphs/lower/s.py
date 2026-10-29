"""Mixed glyph s — stacked anatomy open_bowl pair (P3-7)."""

from __future__ import annotations

from elements import WIDTHS, zone_anchors

from typekernel.anatomy import open_bowl
from typekernel.project import glyph
from typekernel.system import System


@glyph("s", group="lc.mixed")
def s(system: System):
    st = float(system.stem["lc"])
    thin = float(system.stem.get("lc_h", st * 0.85))
    xh = float(system.zones.x)
    width = float(WIDTHS["s"])
    lsb = float(system.tokens.get("lsb_lc", 40.0))
    ov = float(system.overshoot.round)
    exp = float(system.tokens.get("bowl_exponent", 2.15))
    aperture = float(system.tokens.get("bowl_aperture", 0.42))
    tension = float(system.tokens.get("shoulder_tension", 0.55))
    cx = lsb + width / 2.0
    rx = width / 2.0 * 0.95
    overlap = st * 0.55
    ry = max(xh * 0.30, (xh + 2.0 * ov + overlap) / 4.0)
    upper = open_bowl(
        (cx, (xh + ov) - ry),
        rx,
        ry,
        thick=st,
        thin=thin,
        aperture=aperture,
        open_side="right",
        exponent=exp,
        overshoot=0.0,
        tension=tension,
        name="bowl.t",
        aperture_index=0,
    )
    lower = open_bowl(
        (cx, (-ov) + ry),
        rx,
        ry,
        thick=st,
        thin=thin,
        aperture=aperture,
        open_side="left",
        exponent=exp,
        overshoot=0.0,
        tension=tension,
        name="bowl.b",
        aperture_index=1,
    )
    return zone_anchors(upper + lower, system, top='x')
