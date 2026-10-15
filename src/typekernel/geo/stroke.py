"""Midline / centerline expand with constant or contrast (elliptical) pens.

Construction-layer geometry: a skeleton path thickened by a pen into a closed
outline. This is **not** a weight axis and must not be named or used as
``buffer`` / ``expand_stroke_weight``. Bold/Light still belong in ``axes``.

Agent-facing entry points:

- :class:`Pen` — circular (``contrast=1``) or elliptical contrast pen
- :class:`Centerline` — open or closed polyline skeleton
- :class:`CubicCenterline` — cubic Bézier midline (TK-308 spike)
- :func:`expand` — offset the centerline by the pen with join/cap options
- :func:`expand_cubic` — flatten a cubic midline, expand, and report chord error
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Literal

from typekernel.geo.outline import Outline
from typekernel.geo.path_builder import PathBuilder
from typekernel.geo.segment import CubicSegment

JoinStyle = Literal["miter", "round", "bevel"]
CapStyle = Literal["butt", "round", "square"]

# Path token: a point, or an arc marker ("arc", cx, cy, ax, ay, bx, by).
PointTok = tuple[float, float]
ArcTok = tuple[str, float, float, float, float, float, float]
Token = PointTok | ArcTok

_EPS = 1e-9

__all__ = [
    "CapStyle",
    "Centerline",
    "CenterlineExpandReport",
    "CubicBezier",
    "CubicCenterline",
    "JoinStyle",
    "Pen",
    "cubic_centerline_to_polyline",
    "expand",
    "expand_cubic",
    "flatten_cubic_centerline",
]


@dataclass(frozen=True, slots=True)
class Pen:
    """Elliptical (or circular) construction pen.

    Attributes:
        thickness: Full width of a **vertical** stroke (design units). Equals
            the horizontal diameter of the pen ellipse.
        contrast: Horizontal-to-vertical ratio. ``1.0`` is a circular pen;
            values below 1 make horizontal strokes thinner than vertical ones.
        angle_deg: Pen rotation in degrees (0 = axes-aligned ellipse).
    """

    thickness: float
    contrast: float = 1.0
    angle_deg: float = 0.0

    def __post_init__(self) -> None:
        if self.thickness <= 0:
            raise ValueError(f"thickness must be positive, got {self.thickness!r}")
        if self.contrast <= 0:
            raise ValueError(f"contrast must be positive, got {self.contrast!r}")

    @property
    def rx(self) -> float:
        """Horizontal semi-axis (vertical strokes measure ``2 * rx``)."""
        return self.thickness / 2.0

    @property
    def ry(self) -> float:
        """Vertical semi-axis (horizontal strokes measure ``2 * ry``)."""
        return self.thickness * self.contrast / 2.0

    def half_width(self, normal_x: float, normal_y: float) -> float:
        """Perpendicular half-thickness for a unit outward normal.

        Ellipse support ``h(u) = sqrt(rx² ux² + ry² uy²)`` after rotating
        ``u`` into pen space by ``-angle_deg``.
        """
        ln = math.hypot(normal_x, normal_y)
        if ln < _EPS:
            return self.rx
        ux, uy = normal_x / ln, normal_y / ln
        if abs(self.angle_deg) > _EPS:
            rad = math.radians(-self.angle_deg)
            c, s = math.cos(rad), math.sin(rad)
            ux, uy = c * ux - s * uy, s * ux + c * uy
        return math.hypot(self.rx * ux, self.ry * uy)


@dataclass(frozen=True, slots=True)
class Centerline:
    """Polyline skeleton (open or closed)."""

    points: tuple[tuple[float, float], ...]
    closed: bool = False

    def __post_init__(self) -> None:
        if len(self.points) < 2:
            raise ValueError("centerline needs at least two points")

    @classmethod
    def from_points(
        cls,
        points: Sequence[tuple[float, float]],
        *,
        closed: bool = False,
    ) -> Centerline:
        return cls(tuple((float(x), float(y)) for x, y in points), closed=closed)


@dataclass(frozen=True, slots=True)
class CubicBezier:
    """Single cubic Bézier segment (``p0`` → ``p3``, handles ``p1`` / ``p2``)."""

    p0: tuple[float, float]
    p1: tuple[float, float]
    p2: tuple[float, float]
    p3: tuple[float, float]

    @classmethod
    def line(
        cls,
        a: tuple[float, float],
        b: tuple[float, float],
    ) -> CubicBezier:
        return cls(a, a, b, b)


@dataclass(frozen=True, slots=True)
class CubicCenterline:
    """Cubic midline path (construction only; not wired into default glyph pipeline)."""

    segments: tuple[CubicBezier, ...]
    closed: bool = False

    def __post_init__(self) -> None:
        if not self.segments:
            raise ValueError("cubic centerline needs at least one segment")

    @classmethod
    def from_beziers(
        cls,
        segments: Sequence[CubicBezier],
        *,
        closed: bool = False,
    ) -> CubicCenterline:
        return cls(tuple(segments), closed=closed)


@dataclass(frozen=True, slots=True)
class CenterlineExpandReport:
    """Honest cost of expanding a cubic midline via flattening + polyline offset.

    The offset of a cubic under an elliptical pen is generally not cubic; this
    report records how closely the **centerline** was approximated before the
    existing polyline expand runs. Round joins/caps still emit cubics on output.
    """

    max_chord_error: float
    cubic_segment_count: int
    polyline_vertex_count: int
    outline_cubic_segment_count: int
    chord_budget: float
    max_offset_fit_error: float = 0.0
    """Max sampled offset-rail distance to fitted cubics (0 when flatten path used)."""


def _mid(
    a: tuple[float, float], b: tuple[float, float]
) -> tuple[float, float]:
    return ((a[0] + b[0]) / 2.0, (a[1] + b[1]) / 2.0)


def _point_line_distance(
    p: tuple[float, float],
    a: tuple[float, float],
    b: tuple[float, float],
) -> float:
    ax, ay = a
    bx, by = b
    px, py = p
    dx, dy = bx - ax, by - ay
    ln2 = dx * dx + dy * dy
    if ln2 < _EPS:
        return math.hypot(px - ax, py - ay)
    t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / ln2))
    qx = ax + t * dx
    qy = ay + t * dy
    return math.hypot(px - qx, py - qy)


def _split_cubic(seg: CubicBezier) -> tuple[CubicBezier, CubicBezier]:
    p0, p1, p2, p3 = seg.p0, seg.p1, seg.p2, seg.p3
    m01 = _mid(p0, p1)
    m12 = _mid(p1, p2)
    m23 = _mid(p2, p3)
    m012 = _mid(m01, m12)
    m123 = _mid(m12, m23)
    m = _mid(m012, m123)
    return CubicBezier(p0, m01, m012, m), CubicBezier(m, m123, m23, p3)


def _flatten_cubic_segment(
    seg: CubicBezier,
    budget: float,
    pts: list[tuple[float, float]],
    max_err: list[float],
) -> None:
    d1 = _point_line_distance(seg.p1, seg.p0, seg.p3)
    d2 = _point_line_distance(seg.p2, seg.p0, seg.p3)
    err = max(d1, d2)
    if err <= budget:
        if not pts or pts[-1] != seg.p0:
            pts.append(seg.p0)
        if pts[-1] != seg.p3:
            pts.append(seg.p3)
        max_err[0] = max(max_err[0], err)
        return
    left, right = _split_cubic(seg)
    _flatten_cubic_segment(left, budget, pts, max_err)
    _flatten_cubic_segment(right, budget, pts, max_err)


def cubic_centerline_to_polyline(
    centerline: CubicCenterline,
    chord_budget: float = 0.35,
) -> Centerline:
    """Polyline approximation of a cubic midline (for chaining to :func:`expand`)."""
    poly, _ = flatten_cubic_centerline(centerline, chord_budget)
    return poly


def flatten_cubic_centerline(
    centerline: CubicCenterline,
    chord_budget: float = 0.35,
) -> tuple[Centerline, CenterlineExpandReport]:
    """Approximate a cubic midline as a polyline within ``chord_budget``."""
    if chord_budget <= 0:
        raise ValueError(f"chord_budget must be positive, got {chord_budget!r}")
    pts: list[tuple[float, float]] = []
    max_err = [0.0]
    for seg in centerline.segments:
        _flatten_cubic_segment(seg, chord_budget, pts, max_err)
    if centerline.closed and pts and pts[0] != pts[-1]:
        pts.append(pts[0])
    poly = Centerline(tuple(pts), closed=centerline.closed)
    return poly, CenterlineExpandReport(
        max_chord_error=max_err[0],
        cubic_segment_count=len(centerline.segments),
        polyline_vertex_count=len(pts),
        outline_cubic_segment_count=0,
        chord_budget=chord_budget,
    )


def _outline_cubic_segment_count(outline: Outline) -> int:
    return sum(
        1
        for contour in outline.contours
        for segment in contour.segments
        if isinstance(segment, CubicSegment)
    )


def _cubic_eval(seg: CubicBezier, t: float) -> tuple[float, float]:
    u = 1.0 - t
    p0, p1, p2, p3 = seg.p0, seg.p1, seg.p2, seg.p3
    return (
        u**3 * p0[0]
        + 3 * u**2 * t * p1[0]
        + 3 * u * t**2 * p2[0]
        + t**3 * p3[0],
        u**3 * p0[1]
        + 3 * u**2 * t * p1[1]
        + 3 * u * t**2 * p2[1]
        + t**3 * p3[1],
    )


def _cubic_deriv_eval(seg: CubicBezier, t: float) -> tuple[float, float]:
    u = 1.0 - t
    p0, p1, p2, p3 = seg.p0, seg.p1, seg.p2, seg.p3
    return (
        3 * u**2 * (p1[0] - p0[0])
        + 6 * u * t * (p2[0] - p1[0])
        + 3 * t**2 * (p3[0] - p2[0]),
        3 * u**2 * (p1[1] - p0[1])
        + 6 * u * t * (p2[1] - p1[1])
        + 3 * t**2 * (p3[1] - p2[1]),
    )


def _sample_offset_rail(
    seg: CubicBezier,
    pen: Pen,
    samples: int,
    *,
    left_side: bool,
) -> list[tuple[float, float]]:
    if samples < 2:
        raise ValueError("samples must be >= 2")
    pts: list[tuple[float, float]] = []
    for i in range(samples):
        t = i / (samples - 1)
        px, py = _cubic_eval(seg, t)
        dx, dy = _cubic_deriv_eval(seg, t)
        tx, ty = _unit(dx, dy)
        nx, ny = _left(tx, ty) if left_side else _right(tx, ty)
        pts.append(_offset(px, py, nx, ny, pen))
    return pts


def _fit_cubic_endpoints_tangents(
    points: Sequence[tuple[float, float]],
) -> CubicBezier:
    if len(points) < 2:
        raise ValueError("need at least two points to fit")
    p0, p3 = points[0], points[-1]
    if len(points) == 2:
        return CubicBezier.line(p0, p3)
    t0 = _unit(points[1][0] - p0[0], points[1][1] - p0[1])
    t1 = _unit(p3[0] - points[-2][0], p3[1] - points[-2][1])
    chord = math.hypot(p3[0] - p0[0], p3[1] - p0[1])
    alpha = chord / 3.0
    p1 = (p0[0] + t0[0] * alpha, p0[1] + t0[1] * alpha)
    p2 = (p3[0] - t1[0] * alpha, p3[1] - t1[1] * alpha)
    return CubicBezier(p0, p1, p2, p3)


def _distance_point_to_cubic(
    seg: CubicBezier,
    px: float,
    py: float,
    *,
    steps: int = 32,
) -> float:
    best = float("inf")
    for i in range(steps + 1):
        t = i / steps
        x, y = _cubic_eval(seg, t)
        best = min(best, math.hypot(px - x, py - y))
    return best


def _fit_offset_rail(
    points: list[tuple[float, float]],
    budget: float,
    *,
    depth: int = 0,
    max_depth: int = 4,
) -> tuple[list[CubicBezier], float]:
    fit = _fit_cubic_endpoints_tangents(points)
    err = max(_distance_point_to_cubic(fit, p[0], p[1]) for p in points)
    if err <= budget or depth >= max_depth or len(points) < 5:
        return [fit], err
    mid = len(points) // 2
    left, err_l = _fit_offset_rail(points[: mid + 1], budget, depth=depth + 1)
    right, err_r = _fit_offset_rail(points[mid:], budget, depth=depth + 1)
    return left + right, max(err_l, err_r)


def _append_cubic_chain(b: PathBuilder, chain: list[CubicBezier]) -> None:
    for seg in chain:
        b.curveTo(seg.p1[0], seg.p1[1], seg.p2[0], seg.p2[1], seg.p3[0], seg.p3[1])


def _expand_closed_cubic_offset(
    centerline: CubicCenterline,
    pen: Pen,
    *,
    offset_fit_budget: float,
    samples: int = 17,
) -> tuple[Outline, float]:
    """Closed cubic midline → annulus (outer + hole) via per-segment rail fits."""
    outer_chains: list[list[CubicBezier]] = []
    inner_chains: list[list[CubicBezier]] = []
    max_err = 0.0
    for seg in centerline.segments:
        left = _sample_offset_rail(seg, pen, samples, left_side=True)
        right = _sample_offset_rail(seg, pen, samples, left_side=False)
        oc, err_o = _fit_offset_rail(right, offset_fit_budget)
        ic, err_i = _fit_offset_rail(left, offset_fit_budget)
        max_err = max(max_err, err_o, err_i)
        outer_chains.append(oc)
        inner_chains.append(ic)
    b = PathBuilder()
    start = outer_chains[0][0].p0
    b.moveTo(start[0], start[1])
    for chain in outer_chains:
        _append_cubic_chain(b, chain)
    b.closePath()
    inner_start = inner_chains[0][0].p0
    b.moveTo(inner_start[0], inner_start[1])
    for chain in reversed(inner_chains):
        for seg_r in reversed(chain):
            b.curveTo(
                seg_r.p2[0],
                seg_r.p2[1],
                seg_r.p1[0],
                seg_r.p1[1],
                seg_r.p0[0],
                seg_r.p0[1],
            )
    b.closePath()
    return b.build(), max_err


def _expand_open_cubic_offset(
    centerline: CubicCenterline,
    pen: Pen,
    *,
    offset_fit_budget: float,
    samples: int = 17,
) -> tuple[Outline, float]:
    """Open single-segment cubic midline; offset rails as cubic chains + butt caps."""
    seg = centerline.segments[0]
    left = _sample_offset_rail(seg, pen, samples, left_side=True)
    right = _sample_offset_rail(seg, pen, samples, left_side=False)
    left_chain, err_l = _fit_offset_rail(left, offset_fit_budget)
    right_chain, err_r = _fit_offset_rail(right, offset_fit_budget)
    max_err = max(err_l, err_r)
    b = PathBuilder()
    b.moveTo(left[0][0], left[0][1])
    _append_cubic_chain(b, left_chain)
    b.lineTo(right[-1][0], right[-1][1])
    for seg_r in reversed(right_chain):
        b.curveTo(
            seg_r.p2[0],
            seg_r.p2[1],
            seg_r.p1[0],
            seg_r.p1[1],
            seg_r.p0[0],
            seg_r.p0[1],
        )
    b.closePath()
    return b.build(), max_err


def expand_cubic(
    centerline: CubicCenterline,
    pen: Pen,
    *,
    chord_budget: float = 0.35,
    offset_fit_budget: float = 0.75,
    join: JoinStyle = "miter",
    cap: CapStyle = "butt",
    miter_limit: float = 4.0,
) -> tuple[Outline, CenterlineExpandReport]:
    """Expand a cubic midline; output includes cubics at round joins/caps."""
    if join == "miter" and offset_fit_budget > 0:
        if (
            not centerline.closed
            and cap == "butt"
            and len(centerline.segments) == 1
        ):
            outline, fit_err = _expand_open_cubic_offset(
                centerline,
                pen,
                offset_fit_budget=offset_fit_budget,
            )
            return outline, CenterlineExpandReport(
                max_chord_error=0.0,
                cubic_segment_count=1,
                polyline_vertex_count=0,
                outline_cubic_segment_count=_outline_cubic_segment_count(outline),
                chord_budget=chord_budget,
                max_offset_fit_error=fit_err,
            )
        if centerline.closed:
            outline, fit_err = _expand_closed_cubic_offset(
                centerline,
                pen,
                offset_fit_budget=offset_fit_budget,
            )
            return outline, CenterlineExpandReport(
                max_chord_error=0.0,
                cubic_segment_count=len(centerline.segments),
                polyline_vertex_count=0,
                outline_cubic_segment_count=_outline_cubic_segment_count(outline),
                chord_budget=chord_budget,
                max_offset_fit_error=fit_err,
            )

    poly, report = flatten_cubic_centerline(centerline, chord_budget)
    outline = expand(
        poly,
        pen,
        join=join,
        cap=cap,
        miter_limit=miter_limit,
    )
    return outline, CenterlineExpandReport(
        max_chord_error=report.max_chord_error,
        cubic_segment_count=report.cubic_segment_count,
        polyline_vertex_count=report.polyline_vertex_count,
        outline_cubic_segment_count=_outline_cubic_segment_count(outline),
        chord_budget=chord_budget,
        max_offset_fit_error=0.0,
    )


def expand(
    centerline: Centerline | Sequence[tuple[float, float]],
    pen: Pen,
    *,
    join: JoinStyle = "miter",
    cap: CapStyle = "butt",
    miter_limit: float = 4.0,
) -> Outline:
    """Expand a centerline by ``pen`` into a closed outline.

    ``join``: ``miter`` | ``round`` | ``bevel`` at interior vertices.
    ``cap``: ``butt`` | ``round`` | ``square`` at open ends (ignored if closed).
    ``miter_limit``: clips miters longer than ``limit * half_width`` to a bevel.
    """
    if join not in ("miter", "round", "bevel"):
        raise ValueError(f"unknown join style: {join!r}")
    if cap not in ("butt", "round", "square"):
        raise ValueError(f"unknown cap style: {cap!r}")
    if miter_limit < 1.0:
        raise ValueError(f"miter_limit must be >= 1, got {miter_limit!r}")

    cl = (
        centerline
        if isinstance(centerline, Centerline)
        else Centerline.from_points(centerline)
    )
    pts = [(p[0], p[1]) for p in cl.points]
    if cl.closed:
        return _expand_closed(pts, pen, join=join, miter_limit=miter_limit)
    return _expand_open(pts, pen, join=join, cap=cap, miter_limit=miter_limit)


# --- vector helpers ---------------------------------------------------------


def _unit(dx: float, dy: float) -> tuple[float, float]:
    ln = math.hypot(dx, dy)
    if ln < _EPS:
        return (1.0, 0.0)
    return (dx / ln, dy / ln)


def _left(tx: float, ty: float) -> tuple[float, float]:
    return (-ty, tx)


def _right(tx: float, ty: float) -> tuple[float, float]:
    return (ty, -tx)


def _offset(
    px: float, py: float, nx: float, ny: float, pen: Pen
) -> tuple[float, float]:
    hw = pen.half_width(nx, ny)
    return (px + nx * hw, py + ny * hw)


def _intersect(
    p: tuple[float, float],
    d: tuple[float, float],
    q: tuple[float, float],
    e: tuple[float, float],
) -> tuple[float, float] | None:
    den = d[0] * e[1] - d[1] * e[0]
    if abs(den) < _EPS:
        return None
    s = ((q[0] - p[0]) * e[1] - (q[1] - p[1]) * e[0]) / den
    return (p[0] + d[0] * s, p[1] + d[1] * s)


def _edge_tangents(
    pts: list[tuple[float, float]], *, closed: bool
) -> list[tuple[float, float]]:
    n = len(pts)
    count = n if closed else n - 1
    out: list[tuple[float, float]] = []
    for i in range(count):
        a, b = pts[i], pts[(i + 1) % n]
        out.append(_unit(b[0] - a[0], b[1] - a[1]))
    return out


# --- join / cap geometry ----------------------------------------------------


def _side_join(
    vertex: tuple[float, float],
    t_in: tuple[float, float],
    t_out: tuple[float, float],
    pen: Pen,
    *,
    left_side: bool,
    join: JoinStyle,
    miter_limit: float,
) -> list[Token]:
    """Points (and optional arc markers) for one side at a vertex."""
    n_in = _left(*t_in) if left_side else _right(*t_in)
    n_out = _left(*t_out) if left_side else _right(*t_out)
    a = _offset(vertex[0], vertex[1], n_in[0], n_in[1], pen)
    b = _offset(vertex[0], vertex[1], n_out[0], n_out[1], pen)

    cross = t_in[0] * t_out[1] - t_in[1] * t_out[0]
    dot = t_in[0] * t_out[0] + t_in[1] * t_out[1]
    if abs(cross) < 1e-6 and dot > 0:
        return [a]

    # Outer corner: left side on left turn, right side on right turn
    is_outer = (cross > 0 and left_side) or (cross < 0 and not left_side)

    if not is_outer or join == "bevel":
        if abs(a[0] - b[0]) < _EPS and abs(a[1] - b[1]) < _EPS:
            return [a]
        return [a, b]

    if join == "miter":
        hit = _intersect(a, t_in, b, t_out)
        if hit is None:
            return [a, b]
        hw = (pen.half_width(*n_in) + pen.half_width(*n_out)) / 2.0
        ml = math.hypot(hit[0] - vertex[0], hit[1] - vertex[1])
        if ml > miter_limit * max(hw, _EPS):
            return [a, b]
        return [hit]

    # round outer join
    return [a, ("arc", vertex[0], vertex[1], a[0], a[1], b[0], b[1]), b]


def _emit_arc(
    builder: PathBuilder,
    cx: float,
    cy: float,
    ax: float,
    ay: float,
    bx: float,
    by: float,
    *,
    left_side: bool,
) -> None:
    """Cubic arc from A to B around center C (outer turn direction)."""
    ang0 = math.atan2(ay - cy, ax - cx)
    ang1 = math.atan2(by - cy, bx - cx)
    r0 = math.hypot(ax - cx, ay - cy)
    r1 = math.hypot(bx - cx, by - cy)
    r = (r0 + r1) / 2.0
    da = ang1 - ang0
    while da <= -math.pi:
        da += 2 * math.pi
    while da > math.pi:
        da -= 2 * math.pi
    # Outer: left side prefers CCW (positive); right side prefers CW (negative)
    if left_side and da < 0:
        da += 2 * math.pi
    elif not left_side and da > 0:
        da -= 2 * math.pi
    if abs(da) < 1e-8:
        builder.lineTo(bx, by)
        return
    steps = max(1, math.ceil(abs(da) / (math.pi / 2 + 1e-9)))
    for s in range(steps):
        t0 = ang0 + da * s / steps
        t1 = ang0 + da * (s + 1) / steps
        seg = t1 - t0
        p0x = cx + r * math.cos(t0)
        p0y = cy + r * math.sin(t0)
        p3x = cx + r * math.cos(t1)
        p3y = cy + r * math.sin(t1)
        handle = r * (4.0 / 3.0) * math.tan(seg / 4.0)
        # CCW tangent (-sin, cos); for CW seg<0 handle is negative → correct
        h0x = -math.sin(t0) * handle
        h0y = math.cos(t0) * handle
        h1x = -math.sin(t1) * handle
        h1y = math.cos(t1) * handle
        if s == 0:
            builder.lineTo(p0x, p0y)
        builder.curveTo(p0x + h0x, p0y + h0y, p3x - h1x, p3y - h1y, p3x, p3y)


def _trace_tokens(
    builder: PathBuilder,
    tokens: list[Token],
    *,
    left_side: bool,
    skip_first: bool = True,
) -> None:
    """Emit tokens. If ``skip_first``, the first point is assumed current."""
    first_point = True
    for tok in tokens:
        if len(tok) == 7 and tok[0] == "arc":
            _emit_arc(
                builder,
                tok[1],
                tok[2],
                tok[3],
                tok[4],
                tok[5],
                tok[6],
                left_side=left_side,
            )
            first_point = False
            continue
        # PointTok branch (len == 2)
        px = float(tok[0])
        py = float(tok[1])
        if first_point:
            first_point = False
            if skip_first:
                continue
            builder.moveTo(px, py)
        else:
            builder.lineTo(px, py)


def _build_side_tokens(
    pts: list[tuple[float, float]],
    tangents: list[tuple[float, float]],
    pen: Pen,
    *,
    left_side: bool,
    join: JoinStyle,
    miter_limit: float,
    closed: bool,
) -> list[Token]:
    n = len(pts)
    tokens: list[Token] = []
    if closed:
        for i in range(n):
            t_in = tangents[(i - 1) % len(tangents)]
            t_out = tangents[i % len(tangents)]
            tokens.extend(
                _side_join(
                    pts[i],
                    t_in,
                    t_out,
                    pen,
                    left_side=left_side,
                    join=join,
                    miter_limit=miter_limit,
                )
            )
        return tokens

    # open: start offset, joins, end offset
    t0 = tangents[0]
    n0 = _left(*t0) if left_side else _right(*t0)
    tokens.append(_offset(pts[0][0], pts[0][1], n0[0], n0[1], pen))
    for i in range(1, n - 1):
        tokens.extend(
            _side_join(
                pts[i],
                tangents[i - 1],
                tangents[i],
                pen,
                left_side=left_side,
                join=join,
                miter_limit=miter_limit,
            )
        )
    t1 = tangents[-1]
    n1 = _left(*t1) if left_side else _right(*t1)
    tokens.append(_offset(pts[-1][0], pts[-1][1], n1[0], n1[1], pen))
    return tokens


def _emit_cap(
    builder: PathBuilder,
    endpoint: tuple[float, float],
    tangent: tuple[float, float],
    pen: Pen,
    *,
    cap: CapStyle,
    at_start: bool,
) -> None:
    nl = _left(*tangent)
    nr = _right(*tangent)
    left = _offset(endpoint[0], endpoint[1], nl[0], nl[1], pen)
    right = _offset(endpoint[0], endpoint[1], nr[0], nr[1], pen)
    hw = pen.half_width(nl[0], nl[1])
    outward = (-tangent[0], -tangent[1]) if at_start else tangent

    if cap == "butt":
        builder.lineTo(*(left if at_start else right))
        return

    if cap == "square":
        el = (left[0] + outward[0] * hw, left[1] + outward[1] * hw)
        er = (right[0] + outward[0] * hw, right[1] + outward[1] * hw)
        if at_start:
            builder.lineTo(*er)
            builder.lineTo(*el)
            builder.lineTo(*left)
        else:
            builder.lineTo(*el)
            builder.lineTo(*er)
            builder.lineTo(*right)
        return

    # round semicircle from current side to the other
    if at_start:
        _emit_arc(
            builder,
            endpoint[0],
            endpoint[1],
            right[0],
            right[1],
            left[0],
            left[1],
            left_side=True,
        )
    else:
        _emit_arc(
            builder,
            endpoint[0],
            endpoint[1],
            left[0],
            left[1],
            right[0],
            right[1],
            left_side=True,
        )


def _reverse_tokens(tokens: list[Token]) -> list[Token]:
    """Reverse a side token list, flipping arc endpoints."""
    rev: list[Token] = []
    i = len(tokens) - 1
    while i >= 0:
        tok = tokens[i]
        if len(tok) == 7 and tok[0] == "arc":
            rev.append(("arc", tok[1], tok[2], tok[5], tok[6], tok[3], tok[4]))
            i -= 1
            continue
        rev.append(tok)
        i -= 1
    return rev


def _expand_open(
    pts: list[tuple[float, float]],
    pen: Pen,
    *,
    join: JoinStyle,
    cap: CapStyle,
    miter_limit: float,
) -> Outline:
    tangents = _edge_tangents(pts, closed=False)
    left = _build_side_tokens(
        pts, tangents, pen, left_side=True, join=join, miter_limit=miter_limit, closed=False
    )
    right = _build_side_tokens(
        pts, tangents, pen, left_side=False, join=join, miter_limit=miter_limit, closed=False
    )

    b = PathBuilder()
    _trace_tokens(b, left, left_side=True, skip_first=False)
    _emit_cap(b, pts[-1], tangents[-1], pen, cap=cap, at_start=False)

    rev = _reverse_tokens(right)
    _trace_tokens(b, rev, left_side=False, skip_first=True)
    _emit_cap(b, pts[0], tangents[0], pen, cap=cap, at_start=True)
    b.closePath()
    outline = b.build()
    # Font / pathops convention: solid outer contours are CCW (positive area).
    from typekernel.geo.contour import reverse_contour, signed_area

    contours = []
    for c in outline.contours:
        contours.append(c if signed_area(c) >= 0 else reverse_contour(c))
    return Outline(tuple(contours))


def _expand_closed(
    pts: list[tuple[float, float]],
    pen: Pen,
    *,
    join: JoinStyle,
    miter_limit: float,
) -> Outline:
    """Stroke a closed centerline into an annular ribbon (outer + hole).

    Assumes the centerline is oriented CCW around its interior: the right
    parallel is the outer contour, the left parallel (reversed) is the hole.
    """
    tangents = _edge_tangents(pts, closed=True)
    outer = _build_side_tokens(
        pts, tangents, pen, left_side=False, join=join, miter_limit=miter_limit, closed=True
    )
    inner = _build_side_tokens(
        pts, tangents, pen, left_side=True, join=join, miter_limit=miter_limit, closed=True
    )
    b = PathBuilder()
    _trace_tokens(b, outer, left_side=False, skip_first=False)
    first_o = outer[0]
    if len(first_o) == 2:
        b.lineTo(first_o[0], first_o[1])
    b.closePath()
    # Hole: reverse left side for opposite winding
    hole = _reverse_tokens(inner)
    _trace_tokens(b, hole, left_side=True, skip_first=False)
    first_h = hole[0]
    if len(first_h) == 2:
        b.lineTo(first_h[0], first_h[1])
    b.closePath()
    return b.build()
