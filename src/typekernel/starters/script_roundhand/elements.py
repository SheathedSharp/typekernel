"""Roundhand helpers — Stroke DSL + pointed expand (S4)."""

from __future__ import annotations

from typekernel.anatomy.stroke import (
    Stroke,
    entry,
    exit,
    expand_pointed,
    expand_stroke,
    loop,
    overstroke,
)
from typekernel.project.registry import GlyphDraft
from typekernel.system import Intent, System

__all__ = [
    "Stroke",
    "draft_stroke",
    "entry",
    "exit",
    "expand_pointed",
    "expand_stroke",
    "loop",
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


def draft_stroke(
    system: System,
    stroke: Stroke,
    *,
    anchors: dict | None = None,
    pressure: bool | None = None,
) -> GlyphDraft:
    """Expand pointed stroke and attach skeleton for ``tk see --skeleton``.

    Closed paths use constant pointed pen (clean counters); open paths use
    pressure modulation (thin up / thick down) unless ``pressure`` overrides.
    """
    use_pressure = (not stroke.centerline.closed) if pressure is None else bool(pressure)
    if use_pressure:
        drawing = expand_pointed(stroke, system)
    else:
        drawing = expand_stroke(stroke, system, intent=project_intent())
    return GlyphDraft(
        drawing=drawing,
        anchors=anchors or {},
        skeleton=stroke.centerline,
    )


def stem(
    system: System,
    x: float,
    *,
    y0: float = 0.0,
    y1: float | None = None,
) -> GlyphDraft:
    xh = float(system.zones.x if y1 is None else y1)
    # Slight shade curve (downstroke).
    st = Stroke.through(
        [(x, y1 if y1 is not None else xh), (x, (y0 + xh) * 0.55), (x, y0)],
        tangents=[(0, -1), (0, -1), (0, -1)],
        tension=0.9,
    )
    # Map through slant.
    pts = [system.map_xy(px, py) for px, py in [(x, xh), (x, (y0 + xh) * 0.55), (x, y0)]]
    st = Stroke.through(pts, tangents=[(system.slant, -1), (system.slant, -1), (system.slant, -1)], tension=0.9)
    return draft_stroke(
        system,
        st,
        anchors={
            "entry": (*pts[0], 90.0, float(system.stem["lc"])),
            "exit": (*pts[-1], 90.0, float(system.stem["lc_h"])),
        },
        pressure=False,
    )


def n_arch(system: System) -> GlyphDraft:
    st_w = float(system.stem["lc"])
    xh = float(system.zones.x)
    width = float(system.tokens["n_width"])
    lsb = float(system.tokens.get("lsb_lc", 28.0))
    x0 = lsb + st_w * 0.45
    x1 = lsb + width - st_w * 0.45
    # Stem + arch + stem as one Stroke.through
    pts = [system.map_xy(x, y) for x, y in [
        (x0, xh), (x0, 0.0),
        (x0 + (x1 - x0) * 0.5, xh * 0.95),
        (x1, xh), (x1, 0.0),
    ]]
    tans = [
        (system.slant, -1),
        (0.6, 0.2),
        (0.8, 0.0),
        (system.slant, -1),
        (system.slant, -1),
    ]
    stroke = Stroke.through(pts, tangents=tans, tension=1.0)
    return draft_stroke(
        system,
        stroke,
        anchors={
            "entry": (*pts[0], -90.0, float(system.stem["lc"])),
            "exit": (*pts[-1], -90.0, float(system.stem["lc"])),
        },
    )


def oval(system: System) -> GlyphDraft:
    xh = float(system.zones.x)
    width = float(system.tokens["o_width"])
    lsb = float(system.tokens.get("lsb_lc", 28.0))
    cx = lsb + width * 0.5
    cy = xh * 0.5
    rx, ry = width * 0.38, xh * 0.48
    stroke = loop((cx, cy), rx=rx, ry=ry, start_deg=-60, sweep_deg=360, n=8, tension=1.0)
    # Apply slant to centerline points by rebuilding.
    pts = []
    tans = []
    import math
    for i in range(9):
        ang = math.radians(-60 + 360 * i / 8)
        x, y = cx + rx * math.cos(ang), cy + ry * math.sin(ang)
        pts.append(system.map_xy(x, y))
        tans.append((-rx * math.sin(ang), ry * math.cos(ang)))
    stroke = Stroke.through(pts, tangents=tans, tension=1.05, closed=True)
    return draft_stroke(system, stroke, anchors={
        "entry": (*pts[0], 0.0, float(system.stem["lc_h"])),
        "exit": (*pts[0], 0.0, float(system.stem["lc_h"])),
    })
