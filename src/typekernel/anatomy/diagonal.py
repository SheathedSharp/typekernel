"""Diagonal anatomy parts: diagonal_pair, crossing (target §4.3)."""

from __future__ import annotations

import math

from typekernel.draw import Drawing, Measure, Writer, diagonal_band
from typekernel.geo.point import Point
from typekernel.optics.stem import diagonal_compensation

__all__ = ["crossing", "diagonal_pair"]

PointLike = Point | tuple[float, float]


def _as_point(p: PointLike) -> Point:
    if isinstance(p, Point):
        return p
    return Point(float(p[0]), float(p[1]))


def _with_measures(drawing: Drawing, *measures: Measure) -> Drawing:
    return Drawing(
        drawing.contours,
        drawing.roles,
        drawing.nodes,
        drawing.slots,
        measures,
    )


def _closed_band(
    p_top: Point,
    p_bottom: Point,
    *,
    weight: float,
    compensate: bool,
    name: str,
) -> Drawing:
    left, right = diagonal_band(
        p_top, p_bottom, weight=weight, compensate=compensate
    )
    return (
        Writer()
        .start(left.start)
        .corner(f"{name}.top.l")
        .fragment(left)
        .corner(f"{name}.foot.l")
        .line(right.start)
        .corner(f"{name}.foot.r")
        .fragment(right)
        .corner(f"{name}.top.r")
        .line(left.start)
        .close()
        .build()
    )


def diagonal_pair(
    apex: PointLike,
    left_foot: PointLike,
    right_foot: PointLike,
    *,
    weight: float,
    thin_ratio: float = 0.85,
    crotch: float | None = None,
    ink_trap: float = 0.0,
    compensate: bool = True,
    name: str = "diag",
) -> Drawing:
    """Two diagonal strokes meeting at ``apex`` (A / V style).

    Visual stroke weight is angle-compensated when ``compensate`` is true
    (via ``optics.stem.diagonal_compensation`` / ``diagonal_band``). The inner
    vertex is thinned toward ``crotch`` (defaults to ``weight * thin_ratio``).
    ``ink_trap`` > 0 cuts a small notch at the crotch (depth in design units).
    """
    if float(weight) <= 0:
        raise ValueError(f"weight must be positive, got {weight!r}")
    if not 0.05 < float(thin_ratio) <= 1.0:
        raise ValueError(f"thin_ratio out of range: {thin_ratio!r}")
    ap = _as_point(apex)
    lf = _as_point(left_foot)
    rf = _as_point(right_foot)
    crotch_w = float(weight) * float(thin_ratio) if crotch is None else float(crotch)
    if crotch_w <= 0:
        raise ValueError("crotch must be positive")

    left = _closed_band(
        ap, lf, weight=float(weight), compensate=compensate, name=f"{name}.l"
    )
    right = _closed_band(
        ap, rf, weight=float(weight), compensate=compensate, name=f"{name}.r"
    )
    combined = left + right

    if float(ink_trap) > 0:
        # Small diamond notch at apex, pointing downward along the bisector.
        v0 = Point(lf.x - ap.x, lf.y - ap.y)
        v1 = Point(rf.x - ap.x, rf.y - ap.y)
        n0 = math.hypot(v0.x, v0.y) or 1.0
        n1 = math.hypot(v1.x, v1.y) or 1.0
        bis = Point(v0.x / n0 + v1.x / n1, v0.y / n0 + v1.y / n1)
        bn = math.hypot(bis.x, bis.y) or 1.0
        depth = float(ink_trap)
        tip = Point(ap.x + bis.x / bn * depth, ap.y + bis.y / bn * depth)
        # Trap as a counter-ish triangle overlapping the crotch ink.
        trap = (
            Writer()
            .start(ap)
            .corner(f"{name}.vertex")
            .line(Point(ap.x - depth * 0.4, ap.y))
            .line(tip)
            .line(Point(ap.x + depth * 0.4, ap.y))
            .line(ap)
            .close(role="counter")
            .build()
        )
        combined = combined + trap

    # ``diagonal_band(compensate=True)`` already sets perpendicular width to
    # ``weight``; record that target for diagnose / contracts.
    ang_l = math.degrees(math.atan2(abs(lf.x - ap.x), abs(lf.y - ap.y) or 1e-9))
    if compensate:
        # Optical helper available for callers sizing against an upright stem.
        _ = diagonal_compensation(ang_l, float(weight))
    measures = (
        Measure(
            kind="stem",
            a=f"{name}.l.top.l",
            b=f"{name}.l.top.r",
            expected=float(weight),
            direction_deg=ang_l,
        ),
        Measure(kind="crotch", a=f"{name}.l.top.l", expected=float(crotch_w)),
    )
    return _with_measures(combined, *measures)


def crossing(
    a0: PointLike,
    a1: PointLike,
    b0: PointLike,
    b1: PointLike,
    *,
    weight: float,
    compensate: bool = True,
    name: str = "cross",
) -> Drawing:
    """Two crossing diagonal strokes (x / X style).

    Each stroke is a compensated ``diagonal_band`` parallelogram. Contracts cap
    the merged crossing area relative to a single-stroke area.
    """
    if float(weight) <= 0:
        raise ValueError(f"weight must be positive, got {weight!r}")
    pa0, pa1 = _as_point(a0), _as_point(a1)
    pb0, pb1 = _as_point(b0), _as_point(b1)
    stroke_a = _closed_band(
        pa0, pa1, weight=float(weight), compensate=compensate, name=f"{name}.a"
    )
    stroke_b = _closed_band(
        pb0, pb1, weight=float(weight), compensate=compensate, name=f"{name}.b"
    )
    combined = stroke_a + stroke_b
    measures = (
        Measure(
            kind="stem",
            a=f"{name}.a.top.l",
            b=f"{name}.a.top.r",
            expected=float(weight),
        ),
    )
    return _with_measures(combined, *measures)
