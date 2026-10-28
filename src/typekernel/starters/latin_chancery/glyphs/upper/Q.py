"""Uppercase Q — O + tail."""
from __future__ import annotations

from elements import bowl, stroke

from typekernel.project import glyph
from typekernel.system import System


@glyph("Q", group="uc.round")
def Q(system: System):
    st = float(system.stem["uc"])
    cap = float(system.zones.cap)
    width = float(system.tokens["O_width"])
    lsb = float(system.tokens.get("lsb_uc", 40.0))
    ov = float(system.overshoot.round)
    cx = lsb + width * 0.5
    cy = cap * 0.5
    body = bowl(
        system, cx=cx, cy=cy,
        rx=width * 0.5 - st * 0.1,
        ry=cap * 0.5 + ov - st * 0.05,
        thickness=st,
    )
    tail = stroke(
        system,
        [(cx + width * 0.12, cy - cap * 0.15), (cx + width * 0.42, -40.0)],
        thickness=st * 0.9,
    )
    return body + tail
