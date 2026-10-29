"""Figure 3 — two right-facing bowls stacked."""

from __future__ import annotations

from elements import WIDTHS, bowl, stem_rect

from typekernel.project import glyph
from typekernel.system import System


@glyph("three", group="figs")
def three(system: System):
    st = float(system.stem["lc"])
    width = float(WIDTHS.get("fig", 500))
    lsb = float(system.tokens.get("lsb_lc", 40.0))
    h = float(system.zones.cap) * 0.72
    ov = float(system.overshoot.round) * 0.4
    cx = lsb + width * 0.55
    top = bowl(system, cx=cx, cy=h * 0.70, rx=width * 0.40, ry=h * 0.26 + ov, thickness=st)
    bot = bowl(system, cx=cx, cy=h * 0.30, rx=width * 0.42, ry=h * 0.28 + ov, thickness=st)
    # thin stem spine on the right of bowls for join
    spine = stem_rect(lsb + width - st, lsb + width, h * 0.15, h * 0.85, prefix="three.spine")
    return top + bot + spine
