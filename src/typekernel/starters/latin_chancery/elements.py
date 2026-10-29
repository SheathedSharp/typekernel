"""Chancery project helpers — thin shim over :mod:`typekernel.anatomy.pen`.

Polyline bowls/stroke keep hash-stable expand; flourishes use cubic
:func:`~typekernel.anatomy.pen.stroke_fragment`.
"""

from __future__ import annotations

import math
from collections.abc import Sequence

from fontTools.misc.bezierTools import cubicPointAtT

from typekernel.anatomy.pen import (
    expand_slanted_centerline,
    flourish_entry,
    flourish_exit,
    open_arc_points,
    oval_points,
    pen_dot,
    pen_for_optical_stem,
    project_pen,
    slanted_centerline,
    slanted_vertical_optical_ratio,
)
from typekernel.draw import Drawing, Fragment
from typekernel.geo.segment import CubicSegment, LineSegment
from typekernel.geo.stroke import Centerline
from typekernel.system import System

__all__ = [
    "bowl",
    "flourish_entry",
    "flourish_exit",
    "fragment_polyline",
    "n_arch_points",
    "nest_bowl",
    "open_arc_points",
    "open_bowl",
    "oval_points",
    "pen_dot",
    "pen_for_optical_stem",
    "project_pen",
    "slanted_polyline",
    "slanted_vertical_optical_ratio",
    "stroke",
    "stroke_fragment",
    "u_arch_points",
]


def slanted_polyline(
    points: Sequence[tuple[float, float]],
    system: System,
    *,
    closed: bool = False,
) -> Centerline:
    return slanted_centerline(points, system, closed=closed)


def stroke(
    system: System,
    points: Sequence[tuple[float, float]],
    *,
    closed: bool = False,
    thickness: float | None = None,
) -> Drawing:
    cl = slanted_centerline(points, system, closed=closed)
    return expand_slanted_centerline(system, cl, thickness=thickness)


def bowl(
    system: System,
    *,
    cx: float,
    cy: float,
    rx: float,
    ry: float,
    thickness: float | None = None,
) -> Drawing:
    st = float(system.stem["lc"]) if thickness is None else float(thickness)
    return stroke(system, oval_points(cx, cy, rx, ry, n=48), closed=True, thickness=st)


def open_bowl(
    system: System,
    *,
    cx: float,
    cy: float,
    rx: float,
    ry: float,
    thickness: float | None = None,
    open_side: str = "right",
    aperture_deg: float = 80.0,
    n: int = 36,
) -> Drawing:
    if open_side not in ("right", "left"):
        raise ValueError(f"open_side must be 'right' or 'left', got {open_side!r}")
    st = float(system.stem["lc"]) if thickness is None else float(thickness)
    half = float(aperture_deg) / 2.0
    if open_side == "right":
        start_deg, end_deg = half, 360.0 - half
    else:
        start_deg, end_deg = 180.0 + half, 180.0 - half + 360.0
    return stroke(
        system,
        open_arc_points(cx, cy, rx, ry, start_deg=start_deg, end_deg=end_deg, n=n),
        thickness=st,
    )


def nest_bowl(
    system: System,
    *,
    stem_x: float,
    side: str,
    width: float,
    xh: float,
    lsb: float,
    thickness: float | None = None,
    cy: float | None = None,
    rx: float | None = None,
    ry: float | None = None,
    pull: float = 0.78,
) -> Drawing:
    st = float(system.stem["lc"]) if thickness is None else float(thickness)
    ov = float(system.overshoot.round)
    rx_v = width * 0.36 if rx is None else float(rx)
    ry_v = (xh / 2.0 + ov * 0.45) if ry is None else float(ry)
    cy_v = (xh / 2.0) if cy is None else float(cy)
    if side == "right":
        cx = stem_x + rx_v * float(pull)
    elif side == "left":
        cx = stem_x - rx_v * float(pull)
    else:
        raise ValueError(f"side must be left/right, got {side!r}")
    return bowl(system, cx=cx, cy=cy_v, rx=rx_v, ry=ry_v, thickness=st)


def fragment_polyline(fragment: Fragment, *, samples_per_cubic: int = 8) -> list[tuple[float, float]]:
    pts: list[tuple[float, float]] = []
    for seg in fragment.segments:
        if isinstance(seg, LineSegment):
            for p in (seg.p0, seg.p1):
                pts.append((p.x, p.y))
        elif isinstance(seg, CubicSegment):
            ctrl = [p.as_tuple() for p in seg.points]
            for i in range(samples_per_cubic):
                t = i / (samples_per_cubic - 1)
                x, y = cubicPointAtT(*ctrl, t)
                pts.append((float(x), float(y)))
        else:
            p0 = seg.points[0]
            pts.append((p0.x, p0.y))
    cleaned: list[tuple[float, float]] = []
    for p in pts:
        if not cleaned or math.hypot(p[0] - cleaned[-1][0], p[1] - cleaned[-1][1]) > 0.5:
            cleaned.append(p)
    return cleaned


def stroke_fragment(
    system: System,
    fragment: Fragment,
    *,
    thickness: float | None = None,
) -> Drawing:
    """Expand a flourish Fragment via sampled polyline (hash-stable)."""
    pts = fragment_polyline(fragment)
    if len(pts) < 2:
        raise ValueError("flourish fragment too short to stroke")
    return stroke(system, pts, thickness=thickness)


def n_arch_points(
    x0: float, x1: float, y0: float, y1: float, *, rise: float
) -> list[tuple[float, float]]:
    mid = (x0 + x1) / 2.0
    span = x1 - x0
    return [
        (x0, y0),
        (x0, y1 - rise),
        (x0 + span * 0.18, y1),
        (mid, y1 + rise * 0.2),
        (x1 - span * 0.18, y1),
        (x1, y1 - rise),
        (x1, y0),
    ]


def u_arch_points(
    x0: float, x1: float, y_top: float, *, rise: float
) -> list[tuple[float, float]]:
    mid = (x0 + x1) / 2.0
    span = x1 - x0
    return [
        (x0, y_top),
        (x0, rise),
        (x0 + span * 0.15, 0.0),
        (mid, -rise * 0.15),
        (x1 - span * 0.15, 0.0),
        (x1, rise),
        (x1, y_top),
    ]
