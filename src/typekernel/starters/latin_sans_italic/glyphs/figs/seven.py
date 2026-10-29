"""Figure 7 — top bar + diagonal (interpolation-safe)."""

from __future__ import annotations

from elements import fuse, stroke

from typekernel.project import glyph
from typekernel.system import System


@glyph("seven", group="figs")
def seven(system: System):
    st = float(system.stem["lc"])
    width = float(system.tokens.get("fig_width", 460.0))
    lsb = float(system.tokens["lsb_lc"])
    h = float(system.zones.cap) * 0.72
    top = stroke(system, [(lsb + width * 0.1, h), (lsb + width * 0.9, h)], thickness=st)
    leg = stroke(system, [(lsb + width * 0.9, h), (lsb + width * 0.35, 0.0)], thickness=st)
    return fuse(top + leg)
