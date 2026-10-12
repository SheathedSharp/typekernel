"""Superellipse bowls and tension / bias cubic controls.

General curve primitives for construction — not glyph-specific beauty hacks.

Agent-facing entry points:

- :func:`superellipse_kappa` — handle ratio for a Lamé / superellipse quadrant
- :func:`superellipse_cubics` / :func:`superellipse` — closed cubic contour
- :func:`tune_handles` — scale / bias cubic handles in place
- :func:`tensioned_cubic` — build a cubic from endpoints + tangents with
  tension / bias
"""

from __future__ import annotations

import math
from typing import Literal

from typekernel.geo.contour import Contour
from typekernel.geo.outline import Outline
from typekernel.geo.path_builder import PathBuilder
from typekernel.geo.point import Point
from typekernel.geo.segment import CubicSegment

Quadrant = Literal[0, 1, 2, 3]


def superellipse_kappa(n: float) -> float:
    """Cubic handle ratio for one superellipse quadrant matched at 45°.

    For exponent ``n`` on ``|x/rx|^n + |y/ry|^n = 1``, a single cubic per
    quadrant with axis-aligned handles of length ``k * radius`` passes through
    the parametric mid-point when::

        k = (8 * 2^(-1/n) - 4) / 3

    At ``n=2`` this recovers :data:`~typekernel.geo.path_helpers.KAPPA`
    (ellipse). As ``n → 1`` (diamond) ``k → 0``; as ``n → ∞`` (rectangle)
    ``k → 4/3``.
    """
    if n <= 0:
        raise ValueError(f"superellipse exponent n must be positive, got {n!r}")
    return float((8.0 * (2.0 ** (-1.0 / n)) - 4.0) / 3.0)


def quarter_superellipse_cubics(
    cx: float,
    cy: float,
    rx: float,
    ry: float,
    quadrant: Quadrant,
    *,
    n: float = 2.0,
    tension: float = 1.0,
) -> tuple[Point, Point, Point, Point]:
    """One CCW quadrant of a superellipse as a cubic ``(p0, p1, p2, p3)``.

    ``tension`` multiplies the geometric handle ratio (1 = exact mid-point
    match for the Lamé curve; >1 pushes toward the corner; <1 toward the
    chord).
    """
    if rx <= 0 or ry <= 0:
        raise ValueError(f"rx and ry must be positive, got rx={rx!r} ry={ry!r}")
    if tension <= 0:
        raise ValueError(f"tension must be positive, got {tension!r}")
    k = superellipse_kappa(n) * tension
    ends = (
        (cx + rx, cy, cx, cy + ry),
        (cx, cy + ry, cx - rx, cy),
        (cx - rx, cy, cx, cy - ry),
        (cx, cy - ry, cx + rx, cy),
    )
    # Same axis-aligned handle pattern as ellipse_cubics, with k instead of KAPPA
    handle = (
        (0.0, k * ry, k * rx, 0.0),
        (-k * rx, 0.0, 0.0, k * ry),
        (0.0, -k * ry, -k * rx, 0.0),
        (k * rx, 0.0, 0.0, -k * ry),
    )
    x0, y0, x3, y3 = ends[quadrant]
    dx1, dy1, dx2, dy2 = handle[quadrant]
    return (
        Point(x0, y0),
        Point(x0 + dx1, y0 + dy1),
        Point(x3 + dx2, y3 + dy2),
        Point(x3, y3),
    )


def superellipse_cubics(
    cx: float,
    cy: float,
    rx: float,
    ry: float,
    n: float = 2.0,
    *,
    tension: float = 1.0,
) -> tuple[tuple[Point, Point, Point, Point], ...]:
    """Four CCW superellipse quadrants from ``+x``."""
    return tuple(
        quarter_superellipse_cubics(cx, cy, rx, ry, q, n=n, tension=tension)
        for q in (0, 1, 2, 3)
    )


def superellipse(
    cx: float,
    cy: float,
    rx: float,
    ry: float,
    n: float = 2.0,
    *,
    tension: float = 1.0,
) -> Contour:
    """Closed cubic contour of a Lamé superellipse (CCW from ``+x``)."""
    segs = tuple(
        CubicSegment(*pts)
        for pts in superellipse_cubics(cx, cy, rx, ry, n, tension=tension)
    )
    return Contour(segs, closed=True)


def superellipse_outline(
    cx: float,
    cy: float,
    rx: float,
    ry: float,
    n: float = 2.0,
    *,
    tension: float = 1.0,
) -> Outline:
    """Single-contour :class:`~typekernel.geo.outline.Outline` superellipse."""
    b = PathBuilder()
    cubics = superellipse_cubics(cx, cy, rx, ry, n, tension=tension)
    p0 = cubics[0][0]
    b.moveTo(p0.x, p0.y)
    for pts in cubics:
        b.curveTo(pts[1].x, pts[1].y, pts[2].x, pts[2].y, pts[3].x, pts[3].y)
    b.closePath()
    return b.build()


def tune_handles(
    segment: CubicSegment,
    tension: float = 1.0,
    *,
    bias: float = 0.0,
) -> CubicSegment:
    """Return a cubic with handles scaled by ``tension`` and shifted by ``bias``.

    ``tension`` 1 keeps handle lengths; 0 collapses to the chord; >1 lengthens.
    ``bias`` in ``[-1, 1]`` skews length toward the start (negative) or end
    (positive): outgoing handle at ``p0`` gets ``tension * (1 - bias)``,
    incoming handle at ``p3`` gets ``tension * (1 + bias)`` (each relative to
    the original length, then renormalized so tension=1, bias=0 is identity).
    """
    if tension < 0:
        raise ValueError(f"tension must be >= 0, got {tension!r}")
    if bias < -1.0 or bias > 1.0:
        raise ValueError(f"bias must be in [-1, 1], got {bias!r}")
    p0, p1, p2, p3 = segment.p0, segment.p1, segment.p2, segment.p3
    # Identity shortcut
    if abs(tension - 1.0) < 1e-15 and abs(bias) < 1e-15:
        return segment
    # Scale factors: at bias=0 both get `tension`
    s_out = tension * (1.0 - bias)
    s_in = tension * (1.0 + bias)
    np1 = Point(p0.x + (p1.x - p0.x) * s_out, p0.y + (p1.y - p0.y) * s_out)
    np2 = Point(p3.x + (p2.x - p3.x) * s_in, p3.y + (p2.y - p3.y) * s_in)
    return CubicSegment(p0, np1, np2, p3)


def tensioned_cubic(
    p0: Point,
    p3: Point,
    tangent_in: Point,
    tangent_out: Point,
    *,
    tension: float = 1.0,
    bias: float = 0.0,
    handle_ratio: float = 1.0 / 3.0,
) -> CubicSegment:
    """Cubic between ``p0`` and ``p3`` with tension / bias on handle lengths.

    ``tangent_in`` is the outgoing direction at ``p0``; ``tangent_out`` is the
    incoming direction at ``p3`` (pointing along the path into ``p3``). Base
    handle length is ``handle_ratio * chord``, then multiplied by tension with
    bias skew (same convention as :func:`tune_handles`).
    """
    if tension < 0:
        raise ValueError(f"tension must be >= 0, got {tension!r}")
    if bias < -1.0 or bias > 1.0:
        raise ValueError(f"bias must be in [-1, 1], got {bias!r}")
    chord = math.hypot(p3.x - p0.x, p3.y - p0.y)
    if chord < 1e-12:
        return CubicSegment(p0, p0, p3, p3)
    tin_len = math.hypot(tangent_in.x, tangent_in.y)
    tout_len = math.hypot(tangent_out.x, tangent_out.y)
    if tin_len < 1e-12 or tout_len < 1e-12:
        raise ValueError("tangents must be non-zero")
    u_in = Point(tangent_in.x / tin_len, tangent_in.y / tin_len)
    # tangent_out points toward p3 along the path ⇒ handle p2 sits opposite
    u_out = Point(tangent_out.x / tout_len, tangent_out.y / tout_len)
    base = handle_ratio * chord
    len_out = base * tension * (1.0 - bias)
    len_in = base * tension * (1.0 + bias)
    p1 = Point(p0.x + u_in.x * len_out, p0.y + u_in.y * len_out)
    p2 = Point(p3.x - u_out.x * len_in, p3.y - u_out.y * len_in)
    return CubicSegment(p0, p1, p2, p3)


def tune_contour_handles(
    contour: Contour,
    tension: float = 1.0,
    *,
    bias: float = 0.0,
) -> Contour:
    """Apply :func:`tune_handles` to every cubic in ``contour`` (lines kept)."""
    from typekernel.geo.segment import LineSegment

    out: list[CubicSegment | LineSegment] = []
    for seg in contour.segments:
        if isinstance(seg, CubicSegment):
            out.append(tune_handles(seg, tension, bias=bias))
        else:
            out.append(seg)
    return Contour(tuple(out), closed=contour.closed)
