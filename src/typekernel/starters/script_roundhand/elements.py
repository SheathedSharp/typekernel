"""Roundhand helpers — Stroke DSL + pointed expand (S4).

Join band: entry/exit sit at ``join_y`` (≈0.22·x-height) with near-horizontal
tangents so adjacent Δy stays under ``Metrics.join.max_dy``. Open strokes use
constant-width expand by default (pressure was fracturing islands and breaking
``tk read`` topology priors).
"""

from __future__ import annotations

import math

from typekernel.anatomy.stroke import (
    Stroke,
    entry,
    exit,
    expand_pointed,
    expand_stroke,
    loop,
    overstroke,
)
from typekernel.draw import Drawing
from typekernel.project.registry import GlyphDraft
from typekernel.system import Intent, System

__all__ = [
    "Stroke",
    "draft_stroke",
    "entry",
    "exit",
    "expand_pointed",
    "expand_stroke",
    "join_anchors",
    "join_y",
    "loop",
    "merge_drafts",
    "n_arch",
    "oval",
    "overstroke",
    "project_intent",
    "stem",
]


def project_intent() -> Intent:
    try:
        from project import BRIEF

        return BRIEF.intent
    except Exception:  # noqa: BLE001
        return Intent(
            contrast="high",
            slant="italic",
            tool="pointed",
            connection="full",
            genre="roundhand",
            pen_angle_deg=28.0,
        )


def join_y(system: System) -> float:
    """Shared connecting-band height (design units, pre-slant)."""
    return float(system.zones.x) * 0.22


def join_anchors(
    system: System,
    entry_xy: tuple[float, float],
    exit_xy: tuple[float, float],
    *,
    entry_angle: float = 0.0,
    exit_angle: float = 0.0,
) -> dict[str, tuple[float, float, float, float]]:
    """Map design-space points through slant; width from hairline stem."""
    w = float(system.stem["lc_h"])
    ex = system.map_xy(*entry_xy)
    xo = system.map_xy(*exit_xy)
    return {
        "entry": (float(ex[0]), float(ex[1]), float(entry_angle), w),
        "exit": (float(xo[0]), float(xo[1]), float(exit_angle), w),
    }


def draft_stroke(
    system: System,
    stroke: Stroke,
    *,
    anchors: dict | None = None,
    pressure: bool | None = None,
) -> GlyphDraft:
    """Expand stroke; default open paths to constant width (topology-clean)."""
    # Closed → constant pen. Open → constant unless caller asks for pressure.
    use_pressure = False if pressure is None else bool(pressure)
    if stroke.centerline.closed:
        use_pressure = False
    if use_pressure:
        drawing = expand_pointed(stroke, system)
    else:
        drawing = expand_stroke(stroke, system, intent=project_intent())
    return GlyphDraft(
        drawing=drawing,
        anchors=anchors or {},
        skeleton=stroke.centerline,
    )


def merge_drafts(
    *drafts: GlyphDraft,
    anchors: dict | None = None,
    skeleton: object | None = None,
) -> GlyphDraft:
    """Overlap-construct several stroke drafts into one glyph."""
    if not drafts:
        raise ValueError("merge_drafts needs ≥1 draft")
    drawing: Drawing = drafts[0].drawing
    for d in drafts[1:]:
        drawing = drawing + d.drawing
    skel = skeleton if skeleton is not None else drafts[0].skeleton
    return GlyphDraft(drawing=drawing, anchors=anchors or {}, skeleton=skel)


def stem(
    system: System,
    x: float,
    *,
    y0: float | None = None,
    y1: float | None = None,
) -> GlyphDraft:
    xh = float(system.zones.x)
    jy = join_y(system)
    y_bot = jy if y0 is None else float(y0)
    y_top = xh if y1 is None else float(y1)
    pts = [system.map_xy(px, py) for px, py in [(x, y_top), (x, (y_bot + y_top) * 0.5), (x, y_bot)]]
    st = Stroke.through(
        pts,
        tangents=[(system.slant, -1), (system.slant, -1), (system.slant, -1)],
        tension=0.9,
    )
    return draft_stroke(
        system,
        st,
        anchors=join_anchors(system, (x, y_bot), (x, y_bot)),
        pressure=False,
    )


def n_arch(system: System) -> GlyphDraft:
    """n: entry at join band → up → arch → down → exit at join band."""
    st_w = float(system.stem["lc"])
    xh = float(system.zones.x)
    width = float(system.tokens["n_width"])
    lsb = float(system.tokens.get("lsb_lc", 28.0))
    jy = join_y(system)
    x0 = lsb + st_w * 0.45
    x1 = lsb + width - st_w * 0.45
    pts = [
        system.map_xy(x, y)
        for x, y in [
            (x0, jy),
            (x0, xh),
            (x0 + (x1 - x0) * 0.5, xh * 0.98),
            (x1, xh),
            (x1, jy),
        ]
    ]
    tans = [
        (system.slant, 1),
        (0.5, 0.2),
        (0.9, 0.0),
        (system.slant, -1),
        (1.0, 0.0),
    ]
    stroke = Stroke.through(pts, tangents=tans, tension=1.0)
    return draft_stroke(
        system,
        stroke,
        anchors=join_anchors(system, (x0, jy), (x1, jy)),
        pressure=False,
    )


def oval(system: System) -> GlyphDraft:
    """o: closed bowl; entry left / exit right on the join band."""
    xh = float(system.zones.x)
    width = float(system.tokens["o_width"])
    lsb = float(system.tokens.get("lsb_lc", 28.0))
    jy = join_y(system)
    cx = lsb + width * 0.5
    cy = xh * 0.5
    rx, ry = width * 0.38, xh * 0.48
    pts: list[tuple[float, float]] = []
    tans: list[tuple[float, float]] = []
    # Start at leftmost point near join band angle.
    for i in range(9):
        ang = math.radians(180 + 360 * i / 8)  # start at left
        x, y = cx + rx * math.cos(ang), cy + ry * math.sin(ang)
        pts.append(system.map_xy(x, y))
        tans.append((-rx * math.sin(ang), ry * math.cos(ang)))
    stroke = Stroke.through(pts, tangents=tans, tension=1.05, closed=True)
    # Join anchors at geometric left/right of oval at join_y (clamped onto ellipse-ish).
    # Use horizontal extremities at cy≈join band via x at join_y on ellipse.
    # y = cy + ry*sinθ; for join_y solve sinθ = (jy-cy)/ry
    s = max(-1.0, min(1.0, (jy - cy) / ry))
    # Prefer the side with smaller |θ| from horizontal mid.
    theta = math.asin(s)
    # left (π - θ) and right (θ) in standard position from +x; our loop used cos/sin from +x.
    xl = cx - rx * math.cos(theta)
    xr = cx + rx * math.cos(theta)
    return draft_stroke(
        system,
        stroke,
        anchors=join_anchors(system, (xl, jy), (xr, jy)),
        pressure=False,
    )
