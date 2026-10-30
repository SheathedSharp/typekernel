"""g — closed upper bowl + shallow descender hook."""

from __future__ import annotations

import math

from elements import Stroke, draft_stroke, join_anchors, join_y, merge_drafts

from typekernel.project import glyph
from typekernel.system import System


@glyph("g", group="lc")
def g(system: System):
    xh = float(system.zones.x)
    desc = -180.0
    w = float(system.tokens.get("o_width", 440)) * 0.85
    lsb = float(system.tokens.get("lsb_lc", 28))
    jy = join_y(system)
    cx, cy = lsb + w * 0.5, xh * 0.55
    rx, ry = w * 0.34, xh * 0.38
    pts = []
    tans = []
    for i in range(9):
        ang = math.radians(180 + 360 * i / 8)
        x, y = cx + rx * math.cos(ang), cy + ry * math.sin(ang)
        pts.append(system.map_xy(x, y))
        tans.append((-rx * math.sin(ang), ry * math.cos(ang)))
    bowl = draft_stroke(
        system,
        Stroke.through(pts, tangents=tans, tension=1.05, closed=True),
        pressure=False,
    )
    ear_pts = [
        system.map_xy(x, y)
        for x, y in [
            (lsb + w * 0.75, xh * 0.35),
            (lsb + w * 0.78, 0.0),
            (lsb + w * 0.55, desc * 0.4),
            (lsb + w * 0.4, desc),
            (lsb + w * 0.28, desc * 0.35),
        ]
    ]
    ear = draft_stroke(system, Stroke.through(ear_pts, tension=1.0), pressure=False)
    s = max(-1.0, min(1.0, (jy - cy) / max(ry, 1.0)))
    theta = math.asin(s)
    xl = cx - rx * math.cos(theta)
    xr = cx + rx * math.cos(theta)
    return merge_drafts(
        bowl,
        ear,
        anchors=join_anchors(system, (xl, jy), (xr, jy)),
        skeleton=bowl.skeleton,
    )
