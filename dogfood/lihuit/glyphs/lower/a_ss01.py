"""a.ss01 — single-story a (P4-3 ss01)."""

from __future__ import annotations

from elements import WIDTHS, zone_anchors

from typekernel.anatomy import bowl, stem
from typekernel.project import glyph
from typekernel.system import System


@glyph("a.ss01", unicodes=(), group="lc.mixed", traits=("x-height",))
def a_ss01(system: System):
    st = float(system.stem["lc"])
    thin = float(system.stem.get("lc_h", st * 0.85))
    xh = float(system.zones.x)
    width = float(WIDTHS["a"])
    lsb = float(system.tokens.get("lsb_lc", 40.0))
    ov = float(system.overshoot.round)
    exp = float(system.tokens.get("bowl_exponent", 2.15))
    # Single-story: bowl + right stem like d/b but x-height only
    right = stem(lsb + width - st, lsb + width, 0.0, xh, name="stem.r")
    cx = lsb + (width - st) * 0.5
    ring = bowl(
        (cx, xh * 0.5),
        (width - st) * 0.55,
        xh * 0.5,
        thick=st,
        thin=thin,
        exponent=exp,
        overshoot=ov * 0.5,
        name="bowl",
    )
    return zone_anchors(ring + right, system, top="x")
