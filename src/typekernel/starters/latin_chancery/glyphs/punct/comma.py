"""comma — period + short flourish tail."""
from __future__ import annotations
from elements import flourish_exit, pen_dot, stroke_fragment
from typekernel.project import glyph
from typekernel.system import System

@glyph("comma", group="punct")
def comma(system: System):
    r = float(system.tokens["dot_radius"])
    lsb = float(system.tokens.get("lsb_lc", 32.0)) * 0.5
    cx = lsb + r
    cy = r * 0.9
    tip = (cx - 25.0, -55.0)
    frag = flourish_exit(system, cx, cy - r * 0.3, tip, depth=40.0)
    return pen_dot(system, cx, cy, radius=r) + stroke_fragment(
        system, frag, thickness=float(system.stem["lc_h"])
    )
