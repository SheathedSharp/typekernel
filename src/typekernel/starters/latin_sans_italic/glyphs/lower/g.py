"""g — upper oval + continuous ear into lower open bowl (interpolation-safe)."""

from __future__ import annotations

from elements import open_arc_points, oval_points, stroke

from typekernel.project import glyph
from typekernel.system import System

_OVAL_N = 48


@glyph("g", group="lc.round")
def g(system: System):
    st = float(system.stem["lc"])
    xh = float(system.zones.x)
    desc = float(system.zones.desc)
    width = float(system.tokens.get("g_width", 420.0))
    lsb = float(system.tokens["lsb_lc"])
    ov = float(system.overshoot.round)

    upper_rx = (width - st * 0.35) / 2.0
    upper_cx = lsb + upper_rx
    upper = stroke(
        system,
        oval_points(upper_cx, xh / 2.0, upper_rx, xh / 2.0 + ov * 0.35, n=_OVAL_N),
        closed=True,
        thickness=st,
    )

    lower_cy = desc / 2.0
    lower_ry = max(abs(desc) / 2.0 - st * 0.2, st * 1.2)
    lower_rx = width / 2.0 * 0.78
    lower_cx = lsb + width / 2.0 - st * 0.05
    ear_x = lower_cx + lower_rx * 0.92
    ear_top = xh * 0.72
    lower_arc = open_arc_points(
        lower_cx,
        lower_cy,
        lower_rx,
        lower_ry,
        start_deg=20.0,
        end_deg=-200.0,
        n=22,
    )
    pts = [(ear_x, ear_top), (ear_x, lower_arc[0][1])] + list(lower_arc)
    ear_lower = stroke(system, pts, thickness=st * 0.95)
    return upper + ear_lower
