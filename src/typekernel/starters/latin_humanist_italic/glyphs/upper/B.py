"""B — stem + far gapped bowls (G-class)."""

from __future__ import annotations

from elements import oval_points, stroke, uc_stem

from typekernel.project import glyph
from typekernel.system import System

_OVAL_N = 32
_GAP = 120.0


@glyph("B", group="uc.round")
def B(system: System):
    uc = float(system.stem["uc"])
    cap = float(system.zones.cap)
    width = float(system.tokens.get("B_width", 560.0))
    lsb = float(system.tokens.get("lsb_uc", 44.0))
    x0 = lsb + uc * 0.5
    stem = uc_stem(system, x0, thickness=uc)
    gap = _GAP
    rx = width * 0.25
    upper = stroke(
        system,
        oval_points(x0 + gap + rx, cap * 0.72, rx, cap * 0.16, n=_OVAL_N),
        closed=True,
        thickness=uc * 0.8,
    )
    lower = stroke(
        system,
        oval_points(x0 + gap + rx * 1.05, cap * 0.25, rx * 1.05, cap * 0.18, n=_OVAL_N),
        closed=True,
        thickness=uc * 0.8,
    )
    return stem + upper + lower
