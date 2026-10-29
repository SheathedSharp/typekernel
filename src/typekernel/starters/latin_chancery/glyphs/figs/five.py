"""Figure 5 — top bar + spine + baseline (interpolation-safe)."""

from __future__ import annotations

from elements import stroke

from typekernel.project import glyph
from typekernel.system import System

_GAP = 80.0


@glyph("five", group="figs")
def five(system: System):
    st = float(system.stem["lc"])
    width = float(system.tokens.get("fig_width", 460.0))
    lsb = float(system.tokens.get("lsb_lc", 32.0))
    h = float(system.zones.cap) * 0.72
    gap = _GAP
    return (
        stroke(system, [(lsb + width * 0.2, h), (lsb + width * 0.85, h)], thickness=st)
        + stroke(system, [(lsb + width * 0.28, h - gap), (lsb + width * 0.28, h * 0.5)], thickness=st)
        + stroke(system, [(lsb + width * 0.2, 0.0), (lsb + width * 0.85, 0.0)], thickness=st)
    )
