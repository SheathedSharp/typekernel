"""semicolon — colon with comma tail on lower."""
from __future__ import annotations
from elements import flourish_exit, pen_dot, stroke_fragment
from typekernel.project import glyph
from typekernel.system import System

@glyph("semicolon", group="punct")
def semicolon(system: System):
    r = float(system.stem.get("lc_h", system.stem["lc"])) * (
        float(system.tokens.get("dot_radius", 28.0)) / 36.0
    )
    xh = float(system.zones.x)
    lsb = float(system.tokens.get("lsb_lc", 32.0)) * 0.5
    cx = lsb + r
    tip = (cx - 25.0, -55.0)
    frag = flourish_exit(system, cx, r * 0.6, tip, depth=40.0)
    return (
        pen_dot(system, cx, xh - r * 0.9)
        + pen_dot(system, cx, r * 0.9)
        + stroke_fragment(system, frag, thickness=float(system.stem["lc_h"]))
    )
