"""S4 Stroke DSL — Hobby-like splines, width curves, script building blocks.

Cold-start agents: prefer ``Stroke.through`` + ``entry`` / ``exit`` / ``loop`` /
``overstroke`` over hand-picked cubic handles. Expand with
:func:`expand_stroke` (Intent-aware pen) or :func:`expand_pointed` (thin
upstroke / thick downstroke).
"""

from __future__ import annotations

import math
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import Literal

from typekernel.draw import Drawing
from typekernel.geo.curves import tensioned_cubic
from typekernel.geo.point import Point
from typekernel.geo.stroke import CubicBezier, CubicCenterline
from typekernel.plugins.construct import expand_skeleton_cubic, pointed_pen
from typekernel.system import Intent, System
from typekernel.system.intent import pen_for_intent

__all__ = [
    "Stroke",
    "entry",
    "exit",
    "expand_pointed",
    "expand_stroke",
    "loop",
    "overstroke",
    "pressure_thickness",
    "width_at",
]

PointLike = tuple[float, float] | Point


def _as_xy(p: PointLike) -> tuple[float, float]:
    if isinstance(p, Point):
        return (float(p.x), float(p.y))
    return (float(p[0]), float(p[1]))


def _as_point(p: PointLike) -> Point:
    x, y = _as_xy(p)
    return Point(x, y)


def _unit(dx: float, dy: float) -> tuple[float, float]:
    ln = math.hypot(dx, dy)
    if ln < 1e-12:
        return (1.0, 0.0)
    return (dx / ln, dy / ln)


def _auto_tangents(
    pts: list[tuple[float, float]],
    *,
    closed: bool,
) -> list[tuple[float, float]]:
    """Chord-bisector tangents (lightweight Hobby stand-in)."""
    n = len(pts)
    out: list[tuple[float, float]] = []
    for i in range(n):
        if closed:
            prev_p = pts[(i - 1) % n]
            next_p = pts[(i + 1) % n]
        else:
            prev_p = pts[i - 1] if i > 0 else pts[i]
            next_p = pts[i + 1] if i + 1 < n else pts[i]
        if prev_p == pts[i] and next_p == pts[i]:
            out.append((1.0, 0.0))
            continue
        if prev_p == pts[i]:
            out.append(_unit(next_p[0] - pts[i][0], next_p[1] - pts[i][1]))
        elif next_p == pts[i]:
            out.append(_unit(pts[i][0] - prev_p[0], pts[i][1] - prev_p[1]))
        else:
            # Average of incoming / outgoing unit chords.
            u0 = _unit(pts[i][0] - prev_p[0], pts[i][1] - prev_p[1])
            u1 = _unit(next_p[0] - pts[i][0], next_p[1] - pts[i][1])
            out.append(_unit(u0[0] + u1[0], u0[1] + u1[1]))
    return out


@dataclass(frozen=True, slots=True)
class Stroke:
    """Cubic skeleton with optional parametric width curve ``w(t)`` on ``[0,1]``."""

    centerline: CubicCenterline
    width: Callable[[float], float] | None = None

    @classmethod
    def through(
        cls,
        points: Sequence[PointLike],
        *,
        tangents: Sequence[PointLike] | None = None,
        tension: float = 1.0,
        closed: bool = False,
        width: Callable[[float], float] | None = None,
    ) -> Stroke:
        """Hobby-like spline through ``points`` (optional per-point tangents).

        ``tangents[i]`` is the path direction at ``points[i]``. When omitted,
        chord-bisector tangents are estimated. ``tension`` scales handle lengths
        (1 ≈ cubic Hermite / Hobby-ish; <1 tighter; >1 looser).
        """
        pts = [_as_xy(p) for p in points]
        if closed and len(pts) < 3:
            raise ValueError("closed Stroke.through needs ≥3 points")
        if not closed and len(pts) < 2:
            raise ValueError("Stroke.through needs ≥2 points")
        if tangents is None:
            tans = _auto_tangents(pts, closed=closed)
        else:
            if len(tangents) != len(pts):
                raise ValueError("tangents must match points length")
            tans = [_as_xy(t) for t in tangents]
        segs: list[CubicBezier] = []
        count = len(pts) if closed else len(pts) - 1
        for i in range(count):
            j = (i + 1) % len(pts)
            p0 = _as_point(pts[i])
            p3 = _as_point(pts[j])
            # Outgoing at i, incoming at j (pointing along path into j).
            tin = Point(tans[i][0], tans[i][1])
            tout = Point(tans[j][0], tans[j][1])
            cubic = tensioned_cubic(p0, p3, tin, tout, tension=float(tension))
            segs.append(
                CubicBezier(
                    (cubic.p0.x, cubic.p0.y),
                    (cubic.p1.x, cubic.p1.y),
                    (cubic.p2.x, cubic.p2.y),
                    (cubic.p3.x, cubic.p3.y),
                )
            )
        return cls(centerline=CubicCenterline(tuple(segs), closed=closed), width=width)

    def with_width(self, curve: Callable[[float], float]) -> Stroke:
        """Attach a width curve ``w(t)`` for ``t`` in ``[0, 1]`` along the stroke."""
        return Stroke(centerline=self.centerline, width=curve)


def width_at(stroke: Stroke, t: float, *, default: float) -> float:
    """Sample stroke width at normalized ``t``; fall back to ``default``."""
    if stroke.width is None:
        return float(default)
    return float(stroke.width(max(0.0, min(1.0, float(t)))))


def pressure_thickness(
    dx: float,
    dy: float,
    *,
    thin: float,
    thick: float,
) -> float:
    """Pointed-pen pressure: thick on downstrokes, thin on upstrokes (y-up)."""
    ln = math.hypot(dx, dy)
    if ln < 1e-12:
        return float(thin)
    # Unit direction; descending (dy < 0) → thick.
    uy = dy / ln
    # uy=-1 → 1 (thick); uy=+1 → 0 (thin)
    w = 0.5 * (1.0 - uy)
    return float(thin) + (float(thick) - float(thin)) * w


def expand_stroke(
    stroke: Stroke,
    system: System,
    *,
    intent: Intent | None = None,
    thickness: float | None = None,
) -> Drawing:
    """Expand with Intent-aware pen (broad / pointed / monoline / brush)."""
    optical = float(system.stem["lc"] if thickness is None else thickness)
    if intent is not None:
        pen = pen_for_intent(intent, optical)
    else:
        from typekernel.anatomy.pen import pen_for_optical_stem

        pen = pen_for_optical_stem(system, optical)
    join: Literal["miter", "round", "bevel"] = (
        "bevel" if stroke.centerline.closed else "round"
    )
    drawing, _ = expand_skeleton_cubic(stroke.centerline, pen, join=join, cap="round")
    from typekernel.geo.tidy import tidy_drawing

    return tidy_drawing(drawing)  # type: ignore[return-value]


def expand_pointed(
    stroke: Stroke,
    system: System,
    *,
    thin: float | None = None,
    thick: float | None = None,
) -> Drawing:
    """Expand with direction-sensitive thickness (thin up / thick down).

    Each cubic becomes a short polyline chord expanded with a local pointed
    pen — enough for cold-start roundhand without heavy variable-width deps.
    """
    from typekernel.geo.stroke import flatten_cubic_centerline
    from typekernel.plugins.construct import expand_skeleton

    lc = float(system.stem["lc"])
    th_thin = float(system.stem.get("lc_h", lc * 0.35) if thin is None else thin)
    th_thick = float(lc if thick is None else thick)
    segs = list(stroke.centerline.segments)
    if not segs:
        raise ValueError("expand_pointed: empty skeleton")
    n_seg = len(segs)
    drawings: list[Drawing] = []
    for si, bez in enumerate(segs):
        dx = float(bez.p3[0]) - float(bez.p0[0])
        dy = float(bez.p3[1]) - float(bez.p0[1])
        t_global = (si + 0.5) / n_seg
        if stroke.width is not None:
            w = width_at(stroke, t_global, default=th_thick)
        else:
            w = pressure_thickness(dx, dy, thin=th_thin, thick=th_thick)
        if w <= 1e-6:
            continue
        pen = pointed_pen(w, contrast=1.0, angle_deg=0.0)
        sub = CubicCenterline((bez,), closed=False)
        poly, _report = flatten_cubic_centerline(sub, chord_budget=1.5)
        drawings.append(expand_skeleton(poly, pen, join="round", cap="round"))
    if not drawings:
        raise ValueError("expand_pointed: no drawable segments")
    fused = drawings[0]
    for d in drawings[1:]:
        fused = fused + d
    from typekernel.geo.tidy import tidy_drawing

    return tidy_drawing(fused)  # type: ignore[return-value]



def entry(
    origin: PointLike,
    direction: PointLike,
    *,
    length: float = 80.0,
    curl: float = 0.35,
    tension: float = 1.0,
) -> Stroke:
    """Lead-in stroke into ``origin`` along ``direction`` (unit-ish)."""
    ox, oy = _as_xy(origin)
    dx, dy = _unit(*_as_xy(direction))
    # Start behind origin, with a slight curl opposite the normal.
    nx, ny = -dy, dx
    start = (ox - dx * length + nx * length * curl, oy - dy * length + ny * length * curl)
    mid = (ox - dx * length * 0.45, oy - dy * length * 0.45)
    return Stroke.through(
        [start, mid, (ox, oy)],
        tangents=[(dx, dy), (dx, dy), (dx, dy)],
        tension=tension,
    )


def exit(
    origin: PointLike,
    direction: PointLike,
    *,
    length: float = 90.0,
    curl: float = 0.4,
    tension: float = 1.0,
) -> Stroke:
    """Lead-out stroke from ``origin`` along ``direction``."""
    ox, oy = _as_xy(origin)
    dx, dy = _unit(*_as_xy(direction))
    nx, ny = -dy, dx
    mid = (ox + dx * length * 0.45, oy + dy * length * 0.45)
    end = (ox + dx * length + nx * length * curl, oy + dy * length + ny * length * curl)
    return Stroke.through(
        [(ox, oy), mid, end],
        tangents=[(dx, dy), (dx, dy), (dx, dy)],
        tension=tension,
    )


def loop(
    center: PointLike,
    *,
    rx: float,
    ry: float | None = None,
    start_deg: float = 200.0,
    sweep_deg: float = 300.0,
    n: int = 6,
    tension: float = 1.05,
) -> Stroke:
    """Open loop arc through ``n`` samples (script oval / bowl seed)."""
    cx, cy = _as_xy(center)
    ry_v = float(rx if ry is None else ry)
    pts: list[tuple[float, float]] = []
    tans: list[tuple[float, float]] = []
    for i in range(n + 1):
        ang = math.radians(start_deg + sweep_deg * i / n)
        pts.append((cx + rx * math.cos(ang), cy + ry_v * math.sin(ang)))
        # Tangent ≈ derivative (-rx sin, ry cos)
        tans.append(_unit(-rx * math.sin(ang), ry_v * math.cos(ang)))
    return Stroke.through(pts, tangents=tans, tension=tension, closed=False)


def overstroke(
    a: PointLike,
    b: PointLike,
    *,
    bulge: float = 40.0,
    tension: float = 1.0,
) -> Stroke:
    """Short connecting overstroke from ``a`` to ``b`` with vertical bulge."""
    ax, ay = _as_xy(a)
    bx, by = _as_xy(b)
    mx, my = (ax + bx) / 2.0, (ay + by) / 2.0 + float(bulge)
    return Stroke.through([(ax, ay), (mx, my), (bx, by)], tension=tension)
