"""Chancery helpers — pen_dot, flourish entry/exit, slanted stroke (project-side).

Reuse ``hook`` / ``tensioned_arc`` from draw.construct; do not reimplement
entry / exit / flourish arcs by hand when these helpers fit.
"""

from __future__ import annotations

import math

from fontTools.misc.bezierTools import cubicPointAtT

from typekernel.draw import Drawing, Fragment, hook, tensioned_arc
from typekernel.geo.point import Point
from typekernel.geo.segment import CubicSegment, LineSegment
from typekernel.geo.stroke import Centerline
from typekernel.plugins.construct import broad_nib, expand_skeleton
from typekernel.system import System


def _pen_params(system: System) -> tuple[float, float]:
    contrast = float(system.tokens.get("pen_contrast", 0.28))
    angle = float(system.tokens.get("pen_angle_deg", 38.0))
    return contrast, angle


def project_pen(system: System, thickness: float | None = None):
    """High-contrast broad nib (chancery look via low contrast + angle)."""
    contrast, angle = _pen_params(system)
    th = float(system.stem["lc"] if thickness is None else thickness)
    return broad_nib(th, contrast=contrast, angle_deg=angle)


def slanted_polyline(
    points: list[tuple[float, float]],
    system: System,
    *,
    closed: bool = False,
) -> Centerline:
    slanted = [system.map_xy(x, y) for x, y in points]
    return Centerline.from_points(slanted, closed=closed)


def stroke(
    system: System,
    points: list[tuple[float, float]],
    *,
    closed: bool = False,
    thickness: float | None = None,
) -> Drawing:
    """Expand a pre-slant polyline with the project pen (``System.slant`` applied)."""
    cl = slanted_polyline(points, system, closed=closed)
    optical = float(system.stem["lc"]) if thickness is None else float(thickness)
    pen = project_pen(system, optical)
    join = "bevel" if closed else "round"
    return expand_skeleton(cl, pen, join=join, cap="round")


def pen_dot(
    system: System,
    cx: float,
    cy: float,
    *,
    radius: float | None = None,
) -> Drawing:
    """Tittle / period-style filled dot (closed oval), center in pre-slant space.

    Agents should call this instead of hand-rolling a miniature oval each time.
    """
    r = float(system.tokens["dot_radius"] if radius is None else radius)
    n = 24
    pts = [
        (
            cx + r * math.cos(2.0 * math.pi * i / n),
            cy + r * math.sin(2.0 * math.pi * i / n),
        )
        for i in range(n)
    ]
    thin = float(system.stem.get("lc_h", system.stem["lc"]))
    return stroke(system, pts, closed=True, thickness=thin)


def flourish_exit(
    system: System,
    stem_edge_x: float,
    y_join: float,
    tip: tuple[float, float],
    *,
    depth: float | None = None,
) -> Fragment:
    """Hook-shaped exit flourish from a stem edge (letter-free ``hook``)."""
    d = float(system.tokens["flourish_depth"] if depth is None else depth)
    return hook(stem_edge_x, y_join, Point(*tip), depth=d, tension=0.55)


def flourish_entry(
    system: System,
    p0: tuple[float, float],
    p1: tuple[float, float],
    *,
    tension: float = 0.6,
) -> Fragment:
    """Lead-in arc into a stem (``tensioned_arc``)."""
    a = Point(*p0)
    b = Point(*p1)
    return tensioned_arc(a, Point(0.35, 1.0), b, Point(0.0, 1.0), tension=tension)


def fragment_polyline(fragment: Fragment, *, samples_per_cubic: int = 8) -> list[tuple[float, float]]:
    """Sample a Fragment into pre-slant polyline points for ``stroke``."""
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
    """Expand a flourish Fragment with the project pen."""
    pts = fragment_polyline(fragment)
    if len(pts) < 2:
        raise ValueError("flourish fragment too short to stroke")
    return stroke(system, pts, thickness=thickness)


def oval_points(
    cx: float, cy: float, rx: float, ry: float, *, n: int = 48
) -> list[tuple[float, float]]:
    return [
        (cx + rx * math.cos(2.0 * math.pi * i / n), cy + ry * math.sin(2.0 * math.pi * i / n))
        for i in range(n)
    ]


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
    return stroke(system, oval_points(cx, cy, rx, ry), closed=True, thickness=st)
