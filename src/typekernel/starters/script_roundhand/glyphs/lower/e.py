"""e — closed eye (1 counter); bar as short right-attached spur (no second counter)."""

from __future__ import annotations

import math

from elements import Stroke, draft_stroke, join_anchors, join_y, merge_drafts

from typekernel.project import glyph
from typekernel.system import System


@glyph("e", group="lc")
def e(system: System):
    xh = float(system.zones.x)
    w = float(system.tokens.get("o_width", 440)) * 0.9
    lsb = float(system.tokens.get("lsb_lc", 28))
    jy = join_y(system)
    cx, cy = lsb + w * 0.5, xh * 0.5
    rx, ry = w * 0.36, xh * 0.45
    pts = []
    tans = []
    for i in range(9):
        ang = math.radians(200 + 360 * i / 8)
        x, y = cx + rx * math.cos(ang), cy + ry * math.sin(ang)
        pts.append(system.map_xy(x, y))
        tans.append((-rx * math.sin(ang), ry * math.cos(ang)))
    bowl = draft_stroke(
        system,
        Stroke.through(pts, tangents=tans, tension=1.05, closed=True),
        pressure=False,
    )
    # Short tongue from the left side into the eye — does not bridge to the right.
    tongue = draft_stroke(
        system,
        Stroke.through(
            [
                system.map_xy(lsb + w * 0.22, xh * 0.52),
                system.map_xy(lsb + w * 0.55, xh * 0.52),
            ],
            tension=0.7,
        ),
        pressure=False,
    )
    s = max(-1.0, min(1.0, (jy - cy) / ry))
    theta = math.asin(s)
    xl = cx - rx * math.cos(theta)
    xr = cx + rx * math.cos(theta)
    return merge_drafts(
        bowl,
        tongue,
        anchors=join_anchors(system, (xl, jy), (xr, jy)),
        skeleton=bowl.skeleton,
    )
