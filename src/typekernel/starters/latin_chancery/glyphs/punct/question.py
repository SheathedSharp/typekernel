"""question — open hook + pen_dot."""
from __future__ import annotations

from elements import open_bowl, pen_dot, stroke

from typekernel.project import glyph
from typekernel.system import System


@glyph("question", group="punct")
def question(system: System):
    st = float(system.stem["lc"])
    r = float(system.stem.get("lc_h", st)) * (float(system.tokens.get("dot_radius", 28.0)) / 36.0)
    xh = float(system.zones.x)
    width = float(system.tokens.get("s_width", 340.0))
    lsb = float(system.tokens.get("lsb_lc", 32.0))
    cx = lsb + width * 0.5
    hook = open_bowl(
        system, cx=cx, cy=xh * 0.68, rx=width * 0.4, ry=xh * 0.3,
        thickness=st, open_side="left", aperture_deg=100.0,
    )
    stem = stroke(system, [(cx, xh * 0.45), (cx, r * 3.2)], thickness=st)
    return hook + stem + pen_dot(system, cx, r * 0.9)
