"""Lowercase h — ascender with exit flourish (hook helper)."""

from __future__ import annotations

from elements import flourish_exit, stroke, stroke_fragment

from typekernel.project import glyph
from typekernel.system import System


@glyph("h", group="lc.straight")
def h(system: System):
    st = float(system.stem["lc"])
    xh = float(system.zones.x)
    asc = float(system.zones.asc)
    width = float(system.tokens["h_width"])
    lsb = float(system.tokens.get("lsb_lc", 32.0))
    rise = float(system.tokens.get("arch_rise", 0.14)) * xh
    x0 = lsb + st * 0.5
    x1 = lsb + width - st * 0.5
    mid = (x0 + x1) / 2.0
    body = [
        (x0, asc - 40.0),
        (x0, xh - rise),
        (x0 + (x1 - x0) * 0.18, xh),
        (mid, xh + rise * 0.2),
        (x1 - (x1 - x0) * 0.18, xh),
        (x1, xh - rise),
        (x1, 0.0),
    ]
    drawing = stroke(system, body, thickness=st)
    # Ascender exit flourish (pre-slant coords); tip curls left above asc.
    tip = (x0 - 70.0, asc + 20.0)
    frag = flourish_exit(system, x0, asc - 40.0, tip)
    return drawing + stroke_fragment(system, frag, thickness=float(system.stem["lc_h"]))
