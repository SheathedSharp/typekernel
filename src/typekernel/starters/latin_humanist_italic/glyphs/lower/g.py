"""g — binocular: upper oval + ear + descender bowl (skeleton+pen)."""

from __future__ import annotations

from elements import oval_points, stroke

from typekernel.project import glyph
from typekernel.system import System


@glyph("g", group="lc.round")
def g(system: System):
    st = float(system.stem["lc"])
    xh = float(system.zones.x)
    desc = float(system.zones.desc)
    width = float(system.tokens.get("g_width", 420.0))
    lsb = float(system.tokens.get("lsb_lc", 36.0))
    ov = float(system.overshoot.round)

    upper_rx = (width - st * 0.35) / 2.0
    upper_cx = lsb + upper_rx
    upper = stroke(
        system,
        oval_points(upper_cx, xh / 2.0, upper_rx, xh / 2.0 + ov * 0.35),
        closed=True,
        thickness=st,
    )

    # Keep lower bowl inside desc zone (tol ~24 on ymin).
    lower_cy = desc / 2.0
    lower_ry = abs(desc) / 2.0 - st * 0.15
    lower_rx = width / 2.0 * 0.82
    lower_cx = lsb + width / 2.0 - st * 0.1
    lower = stroke(
        system,
        oval_points(lower_cx, lower_cy, lower_rx, max(lower_ry, st * 1.2)),
        closed=True,
        thickness=st * 0.95,
    )

    ear_x = lsb + width - st * 0.5
    ear = stroke(
        system,
        [(ear_x, lower_cy - lower_ry * 0.1), (ear_x, xh * 0.78)],
        thickness=st,
    )
    return upper + ear + lower
