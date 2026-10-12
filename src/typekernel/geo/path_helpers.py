"""Cubic path construction helpers for common curves.

All helpers emit **cubic** Bézier geometry (or control-point tuples that feed
``PathBuilder.curveTo``). They never flatten to polylines.

The constant :data:`KAPPA` is the classic quarter-circle handle ratio
``4/3 * tan(π/8) ≈ 0.5522847498``. Documented once here; callers should import
it rather than hard-coding a magic float.
"""

from __future__ import annotations

import math
from typing import Literal

from typekernel.geo.point import Point

# 4/3 * tan(π/8) — cubic handle length for a 90° circular arc in unit radius.
KAPPA: float = 0.5522847498307936

Quadrant = Literal[0, 1, 2, 3]
# 0: +x → +y (NE), 1: +y → -x (NW), 2: -x → -y (SW), 3: -y → +x (SE)


def quarter_circle_cubics(
    cx: float,
    cy: float,
    rx: float,
    ry: float,
    quadrant: Quadrant,
) -> tuple[Point, Point, Point, Point]:
    """Return ``(p0, p1, p2, p3)`` for one quarter of an axis-aligned ellipse.

    ``quadrant`` 0 starts at ``(cx+rx, cy)`` and ends at ``(cx, cy+ry)``;
    1, 2, 3 continue counter-clockwise.
    """
    # Endpoints of each quadrant (CCW from +x).
    ends = (
        (cx + rx, cy, cx, cy + ry),
        (cx, cy + ry, cx - rx, cy),
        (cx - rx, cy, cx, cy - ry),
        (cx, cy - ry, cx + rx, cy),
    )
    x0, y0, x3, y3 = ends[quadrant]
    # Handle offsets: kappa along the tangent direction at each end.
    # At +x end tangent is +y; at +y end tangent is -x; etc.
    # p1 = start + (dx1, dy1); p2 = end + (dx2, dy2).
    # Classic kappa handles for CCW quarters (circle exact, ellipse approx):
    #   Q0 (E→N): p1=(cx+rx, cy+k*ry), p2=(cx+k*rx, cy+ry)
    #   Q1 (N→W): p1=(cx-k*rx, cy+ry), p2=(cx-rx, cy+k*ry)
    #   Q2 (W→S): p1=(cx-rx, cy-k*ry), p2=(cx-k*rx, cy-ry)
    #   Q3 (S→E): p1=(cx+k*rx, cy-ry), p2=(cx+rx, cy-k*ry)
    handle = (
        (0.0, KAPPA * ry, KAPPA * rx, 0.0),
        (-KAPPA * rx, 0.0, 0.0, KAPPA * ry),
        (0.0, -KAPPA * ry, -KAPPA * rx, 0.0),
        (KAPPA * rx, 0.0, 0.0, -KAPPA * ry),
    )
    dx1, dy1, dx2, dy2 = handle[quadrant]
    return (
        Point(x0, y0),
        Point(x0 + dx1, y0 + dy1),
        Point(x3 + dx2, y3 + dy2),
        Point(x3, y3),
    )


def ellipse_cubics(
    cx: float,
    cy: float,
    rx: float,
    ry: float,
) -> tuple[tuple[Point, Point, Point, Point], ...]:
    """Four quarter-ellipse cubics forming a closed oval, CCW from ``+x``."""
    quarters: tuple[Quadrant, ...] = (0, 1, 2, 3)
    return tuple(quarter_circle_cubics(cx, cy, rx, ry, q) for q in quarters)


def arc_cubics(
    cx: float,
    cy: float,
    rx: float,
    ry: float,
    start_deg: float,
    end_deg: float,
    *,
    segments: int | None = None,
) -> list[tuple[Point, Point, Point, Point]]:
    """Approximate an elliptical arc from ``start_deg`` to ``end_deg`` with cubics.

    Angles are in degrees, counter-clockwise from ``+x`` (standard math).
    The sweep may be positive or negative; absolute sweep is split into
    pieces of at most 90° (or ``segments`` equal pieces if given).

    Each item is ``(p0, p1, p2, p3)`` suitable for ``curveTo``.
    """
    sweep = end_deg - start_deg
    if sweep == 0.0:
        return []
    abs_sweep = abs(sweep)
    if segments is None:
        segments = max(1, math.ceil(abs_sweep / 90.0 - 1e-12))
    if segments < 1:
        raise ValueError("segments must be >= 1")

    step = sweep / segments
    out: list[tuple[Point, Point, Point, Point]] = []
    for i in range(segments):
        a0 = math.radians(start_deg + i * step)
        a1 = math.radians(start_deg + (i + 1) * step)
        out.append(_unit_arc_cubic(cx, cy, rx, ry, a0, a1))
    return out


def _unit_arc_cubic(
    cx: float,
    cy: float,
    rx: float,
    ry: float,
    a0: float,
    a1: float,
) -> tuple[Point, Point, Point, Point]:
    """One cubic approximating an elliptical arc between two angles (radians)."""
    # Standard alpha for a circular arc of sweep θ:
    #   α = sin(θ) * (√(4 + 3 tan²(θ/2)) - 1) / 3
    # Applied per-axis with rx/ry for an axis-aligned ellipse.
    delta = a1 - a0
    if abs(delta) < 1e-15:
        p = Point(cx + rx * math.cos(a0), cy + ry * math.sin(a0))
        return (p, p, p, p)
    t = math.tan(delta / 2.0)
    alpha = (
        math.sin(delta)
        * (math.sqrt(4.0 + 3.0 * t * t) - 1.0)
        / 3.0
    )
    cos0, sin0 = math.cos(a0), math.sin(a0)
    cos1, sin1 = math.cos(a1), math.sin(a1)
    p0 = Point(cx + rx * cos0, cy + ry * sin0)
    p3 = Point(cx + rx * cos1, cy + ry * sin1)
    # Tangent of ellipse (rx cos θ, ry sin θ) is (-rx sin θ, ry cos θ).
    p1 = Point(p0.x - alpha * rx * sin0, p0.y + alpha * ry * cos0)
    p2 = Point(p3.x + alpha * rx * sin1, p3.y - alpha * ry * cos1)
    return (p0, p1, p2, p3)


def rounded_corner_cubics(
    p_prev: Point,
    corner: Point,
    p_next: Point,
    radius: float,
) -> tuple[Point, Point, Point, Point, Point]:
    """Fillet a sharp corner with one cubic.

    Returns ``(start, c1, c2, end, unused_corner)`` where the path should
    ``lineTo(start)`` (if not already there), then ``curveTo(c1, c2, end)``.
    ``start`` / ``end`` lie on the incoming / outgoing edges at ``radius``
    distance from ``corner`` (clamped if the edge is shorter).

    The fifth value is the original ``corner`` (kept for debugging / asserts).
    """
    if radius < 0:
        raise ValueError(f"radius must be non-negative, got {radius}")
    v_in = Point(corner.x - p_prev.x, corner.y - p_prev.y)
    v_out = Point(p_next.x - corner.x, p_next.y - corner.y)
    len_in = math.hypot(v_in.x, v_in.y)
    len_out = math.hypot(v_out.x, v_out.y)
    if len_in < 1e-12 or len_out < 1e-12:
        raise ValueError("rounded_corner requires non-degenerate edges")
    # Clamp radius so fillets do not pass the far endpoints.
    r = min(radius, len_in * 0.5, len_out * 0.5)
    u_in = Point(v_in.x / len_in, v_in.y / len_in)
    u_out = Point(v_out.x / len_out, v_out.y / len_out)
    start = Point(corner.x - u_in.x * r, corner.y - u_in.y * r)
    end = Point(corner.x + u_out.x * r, corner.y + u_out.y * r)
    # Handles along each edge toward the corner (kappa-scaled for ~circular feel).
    c1 = Point(start.x + u_in.x * r * KAPPA, start.y + u_in.y * r * KAPPA)
    c2 = Point(end.x - u_out.x * r * KAPPA, end.y - u_out.y * r * KAPPA)
    return (start, c1, c2, end, corner)


def smooth_cubic_controls(
    p0: Point,
    p3: Point,
    tangent_in: Point,
    tangent_out: Point,
    *,
    handle_ratio: float = 1.0 / 3.0,
) -> tuple[Point, Point]:
    """Place G1-friendly cubic handles between ``p0`` and ``p3``.

    ``tangent_in`` is the desired outgoing direction at ``p0`` (not necessarily
    unit). ``tangent_out`` is the desired incoming direction at ``p3`` (pointing
    toward the curve, i.e. from p2 toward p3 when normalized — we place p2
    opposite that direction from p3).

    Handle lengths default to ``handle_ratio * chord_length``.
    """
    chord = math.hypot(p3.x - p0.x, p3.y - p0.y)
    if chord < 1e-12:
        return (p0, p3)
    len_h = handle_ratio * chord
    tin_len = math.hypot(tangent_in.x, tangent_in.y)
    tout_len = math.hypot(tangent_out.x, tangent_out.y)
    if tin_len < 1e-12 or tout_len < 1e-12:
        raise ValueError("tangents must be non-zero")
    u_in = Point(tangent_in.x / tin_len, tangent_in.y / tin_len)
    u_out = Point(tangent_out.x / tout_len, tangent_out.y / tout_len)
    p1 = Point(p0.x + u_in.x * len_h, p0.y + u_in.y * len_h)
    # Incoming at p3: handle sits opposite the outgoing tangent_out.
    p2 = Point(p3.x - u_out.x * len_h, p3.y - u_out.y * len_h)
    return (p1, p2)
