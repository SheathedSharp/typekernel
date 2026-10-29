"""question — open hook + thin period (interpolation-safe)."""

from __future__ import annotations

from elements import open_arc_points, oval_points, stroke

from typekernel.project import glyph
from typekernel.system import System

_DOT_N = 16


@glyph("question", group="punct")
def question(system: System):
    st = float(system.stem["lc"])
    xh = float(system.zones.x)
    width = float(system.tokens.get("question_width", 300.0))
    lsb = float(system.tokens["lsb_lc"])
    cx = lsb + width / 2.0
    hook_pts = list(
        open_arc_points(
            cx, xh * 0.72, width * 0.38, xh * 0.28, start_deg=200.0, end_deg=20.0, n=14
        )
    )
    hook_pts += [(cx + width * 0.05, xh * 0.45), (cx, xh * 0.38)]
    hook = stroke(system, hook_pts, thickness=st)
    r = st * 0.55
    dot = stroke(system, oval_points(cx, r, r, r, n=_DOT_N), closed=True, thickness=st * 0.4)
    return hook + dot
