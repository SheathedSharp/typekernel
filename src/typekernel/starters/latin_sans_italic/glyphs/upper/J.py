"""J — stem + shallow gapped hook ."""

from __future__ import annotations

import math

from elements import WIDTHS, stroke

from typekernel.project import glyph
from typekernel.system import System


@glyph("J", group="uc.straight")
def J(system: System):
    uc = float(system.stem["uc"])
    cap = float(system.zones.cap)
    width = float(WIDTHS.get("J", 480.0))
    lsb = float(system.tokens["lsb_uc"])
    x = lsb + width - uc * 0.5
    # Straight stem; shallow hook as separate stroke with gap (deep hooks self-intersection).
    stem = stroke(system, [(x, cap), (x, uc * 1.5)], thickness=uc)
    n = 7
    pts = []
    for i in range(n + 1):
        t = i / n
        pts.append(
            (
                x - width * 0.35 * math.sin(math.pi * 0.5 * t),
                uc * 0.35 + uc * 0.9 * (1.0 - math.cos(math.pi * 0.5 * t)),
            )
        )
    hook = stroke(system, pts, thickness=uc)
    return stem + hook
