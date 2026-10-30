"""a — closed bowl (1 counter) + exit stem on the join band."""

from __future__ import annotations

import math

from elements import Stroke, draft_stroke, join_anchors, join_y, merge_drafts

from typekernel.project import glyph
from typekernel.system import System


@glyph("a", group="lc")
def a(system: System):
    xh = float(system.zones.x)
    w = float(system.tokens.get("n_width", 420)) * 0.9
    lsb = float(system.tokens.get("lsb_lc", 28))
    jy = join_y(system)
    cx, cy = lsb + w * 0.42, xh * 0.48
    rx, ry = w * 0.32, xh * 0.42
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
    sx = lsb + w * 0.72
    stem_pts = [
        system.map_xy(x, y)
        for x, y in [(sx, xh * 0.35), (sx, xh * 0.95), (lsb + w * 0.95, jy)]
    ]
    stem = draft_stroke(
        system, Stroke.through(stem_pts, tension=0.95), pressure=False
    )
    s = max(-1.0, min(1.0, (jy - cy) / ry))
    theta = math.asin(s)
    xl = cx - rx * math.cos(theta)
    return merge_drafts(
        bowl,
        stem,
        anchors=join_anchors(system, (xl, jy), (lsb + w * 0.95, jy)),
        skeleton=bowl.skeleton,
    )
