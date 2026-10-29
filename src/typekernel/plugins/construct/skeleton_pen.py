"""Skeleton + pen construct plugin (ARCHITECTURE.md「构造插件」).

Wraps :mod:`typekernel.geo.stroke` into a :class:`~typekernel.draw.Drawing`.
No letter names — projects supply centerlines; this module only expands pens.
"""

from __future__ import annotations

import math
from collections.abc import Sequence

from typekernel.draw.drawing import ContourRole, Drawing
from typekernel.geo.contour import Contour, reverse_contour, signed_area
from typekernel.geo.point import Point
from typekernel.geo.segment import CubicSegment, LineSegment
from typekernel.geo.stroke import (
    CapStyle,
    Centerline,
    CenterlineExpandReport,
    CubicCenterline,
    JoinStyle,
    Pen,
    expand,
    expand_cubic,
)

__all__ = [
    "broad_nib",
    "densify_polyline",
    "ellipse_point_count",
    "expand_skeleton",
    "expand_skeleton_cubic",
    "pointed_pen",
]


def broad_nib(
    thickness: float,
    *,
    contrast: float = 0.55,
    angle_deg: float = 30.0,
) -> Pen:
    """Elliptical broad-nib pen (contrast < 1, typically rotated)."""
    return Pen(thickness=float(thickness), contrast=float(contrast), angle_deg=float(angle_deg))


def pointed_pen(
    thickness: float,
    *,
    contrast: float = 1.0,
    angle_deg: float = 0.0,
) -> Pen:
    """Near-circular pointed pen (default contrast 1)."""
    return Pen(thickness=float(thickness), contrast=float(contrast), angle_deg=float(angle_deg))




def ellipse_point_count(
    rx: float,
    ry: float,
    *,
    chord_budget: float = 0.5,
    minimum: int = 24,
    maximum: int = 256,
) -> int:
    """Choose oval/arc sample count so polygon chord error stays under budget.

    Agents should not guess ``n=`` for ``oval_points`` — pass this count (or
    rely on :func:`expand_skeleton` densify). ``chord_budget`` is design units.
    """
    import math

    if chord_budget <= 0:
        raise ValueError(f"chord_budget must be positive, got {chord_budget!r}")
    r = max(abs(float(rx)), abs(float(ry)), 1e-6)
    # For a circle, chord length c ≈ 2 r sin(π/n); sagitta ≈ r - r cos(π/n).
    # Require sagitta <= chord_budget → n >= π / acos(1 - budget/r).
    ratio = min(1.0, float(chord_budget) / r)
    # acos domain: 1 - ratio in [-1,1]; when budget >= r, one half is enough.
    n_f = math.pi / max(math.acos(1.0 - ratio), 1e-6)
    n = math.ceil(n_f)
    return max(minimum, min(maximum, n))


def densify_polyline(
    points: Sequence[tuple[float, float]],
    *,
    closed: bool,
    chord_budget: float = 0.5,
) -> list[tuple[float, float]]:
    """Catmull–Rom upsample so consecutive samples are within ``chord_budget``.

    Straight stems with two endpoints stay untouched when the single segment
    is already short enough; curved polylines (ovals, bowls) gain midpoints
    without the project picking ``n``.
    """
    import math

    pts = [(float(p[0]), float(p[1])) for p in points]
    if len(pts) < 2 or chord_budget <= 0:
        return pts

    def _dist(a: tuple[float, float], b: tuple[float, float]) -> float:
        return math.hypot(b[0] - a[0], b[1] - a[1])

    def _at(i: int) -> tuple[float, float]:
        n = len(pts)
        if closed:
            return pts[i % n]
        return pts[max(0, min(n - 1, i))]

    def _cr(
        p0: tuple[float, float],
        p1: tuple[float, float],
        p2: tuple[float, float],
        p3: tuple[float, float],
        t: float,
    ) -> tuple[float, float]:
        t2 = t * t
        t3 = t2 * t
        return (
            0.5
            * (
                (2 * p1[0])
                + (-p0[0] + p2[0]) * t
                + (2 * p0[0] - 5 * p1[0] + 4 * p2[0] - p3[0]) * t2
                + (-p0[0] + 3 * p1[0] - 3 * p2[0] + p3[0]) * t3
            ),
            0.5
            * (
                (2 * p1[1])
                + (-p0[1] + p2[1]) * t
                + (2 * p0[1] - 5 * p1[1] + 4 * p2[1] - p3[1]) * t2
                + (-p0[1] + 3 * p1[1] - 3 * p2[1] + p3[1]) * t3
            ),
        )

    out: list[tuple[float, float]] = []
    n = len(pts)
    seg_count = n if closed else n - 1
    for i in range(seg_count):
        a = _at(i)
        b = _at(i + 1)
        out.append(a)
        length = _dist(a, b)
        if length <= chord_budget:
            continue
        steps = max(1, math.ceil(length / chord_budget))
        p0, p1, p2, p3 = _at(i - 1), a, b, _at(i + 2)
        for s in range(1, steps):
            out.append(_cr(p0, p1, p2, p3, s / steps))
    if not closed:
        out.append(pts[-1])
    return out



_DEGEN_LEN = 1e-9


def _seg_len(seg: LineSegment | CubicSegment) -> float:
    a, b = seg.points[0], seg.points[-1]
    return math.hypot(b.x - a.x, b.y - a.y)


def _drop_degenerate_segments(contour: Contour) -> Contour:
    """Remove near-zero line segments left by elliptical pen joins/caps.

    Project ``apply_slots`` rejects zero-length lines (ARCHITECTURE 槽位与填充协议);
    skeleton expand can emit them at round joins. Dropping them keeps the
    Drawing usable without heal/blend passes.
    """
    kept: list[LineSegment | CubicSegment] = []
    for seg in contour.segments:
        if isinstance(seg, LineSegment) and _seg_len(seg) < _DEGEN_LEN:
            continue
        kept.append(seg)
    if len(kept) < 2:
        return contour
    # Re-stitch endpoints so consecutive segments meet after drops.
    stitched: list[LineSegment | CubicSegment] = []
    for i, seg in enumerate(kept):
        if not stitched:
            stitched.append(seg)
            continue
        prev = stitched[-1]
        prev_end = prev.points[-1]
        start = seg.points[0]
        if abs(prev_end.x - start.x) > 1e-9 or abs(prev_end.y - start.y) > 1e-9:
            # Force shared joint onto prev_end.
            if isinstance(seg, LineSegment):
                seg = LineSegment(prev_end, seg.p1)
            else:
                seg = CubicSegment(prev_end, seg.p1, seg.p2, seg.p3)
        stitched.append(seg)
    if contour.closed and stitched:
        first, last = stitched[0], stitched[-1]
        end = last.points[-1]
        start = first.points[0]
        if abs(end.x - start.x) > 1e-9 or abs(end.y - start.y) > 1e-9:
            if isinstance(last, LineSegment):
                stitched[-1] = LineSegment(last.p0, start)
            else:
                stitched[-1] = CubicSegment(last.p0, last.p1, last.p2, start)
    return Contour(tuple(stitched), closed=contour.closed)


def _line_as_cubic(seg: LineSegment) -> CubicSegment:
    """Promote a line to a cubic with 1/3 collinear handles (geometry unchanged)."""
    p0, p1 = seg.p0, seg.p1
    return CubicSegment(
        p0,
        Point(p0.x + (p1.x - p0.x) / 3.0, p0.y + (p1.y - p0.y) / 3.0),
        Point(p0.x + 2.0 * (p1.x - p0.x) / 3.0, p0.y + 2.0 * (p1.y - p0.y) / 3.0),
        p1,
    )


def _canonicalize_contour(contour: Contour) -> Contour:
    """Promote lines to cubics so expand signatures stay thickness-stable.

    Elliptical ``round`` joins alternate line/cubic emission by pen size; master
    compat (``Drawing.signature``) needs segment *kinds* invariant across weight.
    Counts already match for typical bowls; kinds alone flipped before this step.
    """
    segs: list[LineSegment | CubicSegment] = []
    for seg in contour.segments:
        if isinstance(seg, LineSegment):
            segs.append(_line_as_cubic(seg))
        else:
            segs.append(seg)
    return Contour(tuple(segs), closed=contour.closed)



def _force_closed_endpoints(contour: Contour) -> Contour:
    """Snap the last endpoint to the first so UFO pens do not invent a close line.

    Expand leaves sub-ulp gaps on closed rails; ``closePath`` then inserts an
    extra on-curve point and breaks master ``node_count``.
    """
    if not contour.closed or not contour.segments:
        return contour
    segs = list(contour.segments)
    start = segs[0].points[0]
    last = segs[-1]
    end = last.points[-1]
    if abs(end.x - start.x) <= 1e-6 and abs(end.y - start.y) <= 1e-6:
        if isinstance(last, CubicSegment):
            segs[-1] = CubicSegment(last.p0, last.p1, last.p2, start)
        elif isinstance(last, LineSegment):
            segs[-1] = LineSegment(last.p0, start)
        return Contour(tuple(segs), closed=True)
    return contour

def _normalize_winding(contour: Contour, *, want_positive: bool) -> Contour:
    area = signed_area(contour)
    if area == 0.0:
        return contour
    if (area > 0.0) == want_positive:
        return contour
    return reverse_contour(contour)


def drawing_from_contours(contours: tuple[Contour, ...]) -> Drawing:
    """Assign ink/counter and normalize winding (outer CCW, hole CW).

    A single expanded stroke is always ``ink``. Rings: largest |area| is ink,
    remaining contours are counters.
    """
    if not contours:
        return Drawing((), (), (), slots=())
    contours = tuple(
        _force_closed_endpoints(
            _canonicalize_contour(_drop_degenerate_segments(c))
        )
        for c in contours
    )
    if len(contours) == 1:
        ink = _normalize_winding(contours[0], want_positive=True)
        return Drawing((ink,), ("ink",), ((),), slots=())

    ranked = sorted(
        enumerate(contours),
        key=lambda pair: abs(signed_area(pair[1])),
        reverse=True,
    )
    ordered: list[Contour] = []
    roles: list[ContourRole] = []
    for rank, (_idx, contour) in enumerate(ranked):
        if rank == 0:
            ordered.append(_normalize_winding(contour, want_positive=True))
            roles.append("ink")
        else:
            ordered.append(_normalize_winding(contour, want_positive=False))
            roles.append("counter")
    nodes = tuple(() for _ in ordered)
    return Drawing(tuple(ordered), tuple(roles), nodes, slots=())


def _closed_sampling_minimum(pts: Sequence[tuple[float, float]]) -> tuple[int, float]:
    """Return ``(min_samples, radius)`` for a closed polyline's bounding oval."""
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    rx = (max(xs) - min(xs)) * 0.5
    ry = (max(ys) - min(ys)) * 0.5
    r = max(rx, ry)
    # chord_budget=2.0u catches faceted large bowls; small dots use coarser n.
    return ellipse_point_count(rx, ry, chord_budget=2.0, minimum=16), r


def _require_closed_sampling(
    pts: Sequence[tuple[float, float]],
    *,
    closed: bool,
) -> None:
    """Fail loud on undersampled *large* closed curves.

    Intentional polygons (diamonds, n<8) and small punctuation dots (radius
    under 60) are left alone — agents densify those with chord_budget='auto'
    or pick n via ellipse_point_count when they care. Large bowls with too few
    samples facet under a broad nib and must be fixed at the call site.
    """
    if not closed or len(pts) < 8:
        return
    need, radius = _closed_sampling_minimum(pts)
    if radius < 60.0:
        return
    if len(pts) >= need:
        return
    raise ValueError(
        f"closed centerline has {len(pts)} samples; need ≥ {need} for radius "
        f"~{radius:.0f}. Use ellipse_point_count(rx, ry) for a fixed n shared "
        "across masters, or pass chord_budget=2.0 / chord_budget='auto' to "
        "densify the given polyline (VF-safe only when masters share the same "
        "centerline samples)."
    )


def expand_skeleton(
    centerline: Centerline | Sequence[tuple[float, float]],
    pen: Pen,
    *,
    join: JoinStyle = "round",
    cap: CapStyle = "round",
    miter_limit: float = 4.0,
    chord_budget: float | str | None = None,
) -> Drawing:
    """Expand a polyline skeleton with ``pen`` into a :class:`Drawing`.

    Closed centerlines that yield a ring get ``ink`` + ``counter`` roles from
    winding. Open strokes become a single ``ink`` contour.

    **Closed + ``join='round'`` raises.** Elliptical round joins flip outer/inner
    segment counts across pen weight (ink/counter swap in ``Drawing.signature``),
    which breaks VF. Use ``join='bevel'`` or ``'miter'`` on closed rails; keep
    ``round`` for open strokes/caps.

    ``chord_budget`` densifies the polyline (Catmull–Rom, design units). Default
    ``None`` keeps the given samples and, for closed paths, raises if sampling is
    far below :func:`ellipse_point_count` for the bounding radius. Pass
    ``chord_budget='auto'`` (alias ``2.0``) to densify — VF-safe when masters
    share identical centerline samples; prefer a fixed ``ellipse_point_count``
    ``n`` when master geometry itself scales with stem.
    """
    if isinstance(centerline, Centerline):
        pts = [(p[0], p[1]) for p in centerline.points]
        closed = bool(centerline.closed)
    else:
        pts = [(float(p[0]), float(p[1])) for p in centerline]
        closed = False

    if closed and join == "round":
        raise ValueError(
            "expand_skeleton: join='round' is not allowed on closed centerlines. "
            "Round elliptical joins change segment counts / winding assignment "
            "across pen weight and break Drawing.signature (VF incompat). "
            "Use join='bevel' (preferred) or join='miter' for closed rails; "
            "keep join='round' for open strokes."
        )

    budget: float | None
    if chord_budget is None:
        budget = None
    elif isinstance(chord_budget, str):
        if chord_budget.strip().lower() != "auto":
            raise ValueError(
                f"chord_budget must be None, a positive float, or 'auto'; "
                f"got {chord_budget!r}"
            )
        budget = 2.0
    else:
        budget = float(chord_budget)
        if budget <= 0:
            raise ValueError(f"chord_budget must be positive, got {chord_budget!r}")

    if budget is not None:
        pts = densify_polyline(pts, closed=closed, chord_budget=budget)
        centerline = Centerline.from_points(pts, closed=closed)
    else:
        _require_closed_sampling(pts, closed=closed)
        if isinstance(centerline, Centerline):
            pass
        else:
            centerline = Centerline.from_points(pts, closed=closed)

    outline = expand(
        centerline,
        pen,
        join=join,
        cap=cap,
        miter_limit=miter_limit,
    )
    return drawing_from_contours(outline.contours)


def expand_skeleton_cubic(
    centerline: CubicCenterline,
    pen: Pen,
    *,
    join: JoinStyle = "round",
    cap: CapStyle = "round",
    miter_limit: float = 4.0,
    chord_budget: float = 0.35,
    offset_fit_budget: float = 0.75,
) -> tuple[Drawing, CenterlineExpandReport]:
    """Expand a cubic skeleton; returns ``(Drawing, expand report)``."""
    outline, report = expand_cubic(
        centerline,
        pen,
        join=join,
        cap=cap,
        miter_limit=miter_limit,
        chord_budget=chord_budget,
        offset_fit_budget=offset_fit_budget,
    )
    return drawing_from_contours(outline.contours), report
