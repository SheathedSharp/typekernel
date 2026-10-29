"""Round glyph Q — anatomy bowl + diagonal tail (P3-7)."""

from __future__ import annotations

from elements import WIDTHS, zone_anchors

from typekernel.anatomy import bowl
from typekernel.draw import Writer, diagonal_band
from typekernel.project import glyph
from typekernel.system import System


@glyph("Q", group="uc.round")
def glyph_Q(system: System):
    st = float(system.stem["uc"])
    thin = float(system.stem.get("uc_h", st * 0.85))
    cap = float(system.zones.cap)
    width = float(WIDTHS["Q"])
    lsb = float(system.tokens.get("lsb_uc", 50.0))
    ov = float(system.overshoot.round)
    exp = float(system.tokens.get("bowl_exponent", 2.15))
    cx = lsb + width / 2.0
    cy = cap / 2.0
    rx, ry = width / 2.0, cap / 2.0
    ring = bowl(
        (cx, cy),
        rx,
        ry,
        thick=st,
        thin=thin,
        exponent=exp,
        overshoot=ov,
        name="bowl",
    )
    left, right = diagonal_band(
        (cx + rx * 0.25, cy - ry * 0.35),
        (lsb + width - st * 0.2, -ov * 0.5),
        weight=st,
        compensate=True,
    )
    tail = (
        Writer()
        .start(left.start)
        .corner("tail.top.l")
        .fragment(left)
        .corner("tail.foot.l")
        .line(right.start)
        .corner("tail.foot.r")
        .fragment(right)
        .corner("tail.top.r")
        .line(left.start)
        .close()
        .build()
    )
    return zone_anchors(ring + tail, system, top='cap')
