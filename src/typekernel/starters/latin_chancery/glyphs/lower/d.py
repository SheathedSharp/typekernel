"""d — asc stem + gapped oval (G-class; gap ≥90)."""

from __future__ import annotations

from elements import oval_points, stroke

from typekernel.project import glyph
from typekernel.system import System

_OVAL_N = 48
_GAP = 100.0


@glyph("d", group="lc.round")
def d(system: System):
    st = float(system.stem["lc"])
    xh = float(system.zones.x)
    asc = float(system.zones.asc)
    width = float(system.tokens.get("o_width", 420.0))
    lsb = float(system.tokens.get("lsb_lc", 32.0))
    ov = float(system.overshoot.round)
    x = lsb + width - st * 0.5
    stem = stroke(system, [(x, 0.0), (x, asc)], thickness=st)
    rx = width * 0.32
    cx = x - _GAP - rx
    bowl = stroke(
        system, oval_points(cx, xh / 2.0, rx, xh / 2.0 + ov * 0.35, n=_OVAL_N), closed=True, thickness=st
    )
    return stem + bowl
