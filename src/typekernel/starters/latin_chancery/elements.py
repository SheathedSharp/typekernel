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
    """High-contrast broad nib (chancery look via contrast + angle)."""
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
    """Tittle / period-style filled dot (closed oval), center in pre-slant space."""
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


def open_arc_points(
    cx: float,
    cy: float,
    rx: float,
    ry: float,
    *,
    start_deg: float,
    end_deg: float,
    n: int = 36,
) -> list[tuple[float, float]]:
    a0 = math.radians(start_deg)
    a1 = math.radians(end_deg)
    return [
        (
            cx + rx * math.cos(a0 + (a1 - a0) * i / (n - 1)),
            cy + ry * math.sin(a0 + (a1 - a0) * i / (n - 1)),
        )
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
    """Oval bowl nestled against a stem (``side`` left/right of stem)."""
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


def n_arch_points(
    x0: float, x1: float, y0: float, y1: float, *, rise: float
) -> list[tuple[float, float]]:
    """n-style arch from (x0,y0) up to y1 then down to (x1,y0)."""
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
