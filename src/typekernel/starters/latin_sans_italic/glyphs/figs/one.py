"""Figure 1 — stem with top flag."""

from __future__ import annotations

from elements import fuse, stroke

from typekernel.project import glyph
from typekernel.system import System


@glyph("one", group="figs")
def one(system: System):
    st = float(system.stem["lc"])
    width = float(system.tokens.get("fig_width", 460.0))
    lsb = float(system.tokens["lsb_lc"])
    h = float(system.zones.cap) * 0.72
    x = lsb + width * 0.55
    stem = stroke(system, [(x, 0.0), (x, h)], thickness=st)
    flag = stroke(system, [(x - width * 0.28, h * 0.78), (x, h)], thickness=st)
    return fuse(stem + flag)
