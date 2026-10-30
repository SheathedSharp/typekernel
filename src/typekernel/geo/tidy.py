"""Compile-time contour tidy (S1) — not a post-hoc heal/blend/seal.

``tidy_outline`` re-represents dense pen-expand output as a fixed budget of
cubics (closed contours) or an error-bounded refit (open contours), merges
micro-segments, and drops sliver contours. It runs as part of **construction /
compile** (after pen expand or ``fuse``).

This is **not** the forbidden “事后修缝” path:

* heal / blend / seal / soften patch *topology* or hide bad joins after the
  fact — those remain banned (ARCHITECTURE).
* tidy only *represents* already-intended ink with fewer, G1-friendly cubics.
  It does not invent bridges, close slits, or change winding roles.

Closed contours use a **fixed** cubic count so Light/Bold masters stay
interpolation-compatible; free adaptive refit alone would change segment
counts across weight.
"""

from __future__ import annotations

import math
from collections.abc import Sequence

from typekernel.geo.contour import Contour, reverse_contour, signed_area
from typekernel.geo.outline import Outline
from typekernel.geo.point import Point
from typekernel.geo.segment import CubicSegment, LineSegment
from typekernel.geo.stroke import _contour_sample_polyline

__all__ = [
    "TidyParams",
    "fixed_closed_cubic_refit",
    "merge_short_segments",
    "tidy_drawing",
    "tidy_outline",
]


class TidyParams:
    """Knobs for compile-time tidy (design units unless noted)."""

    __slots__ = (
        "closed_cubics",
        "corner_deg",
        "fit_budget",
        "max_open_cubics",
        "min_step",
        "short_du",
        "sliver_area",
    )

    def __init__(
        self,
        *,
        fit_budget: float = 3.0,
        min_step: float = 3.0,
        corner_deg: float = 35.0,
        short_du: float = 1.5,
        sliver_area: float = 0.0,  # 0 = never drop (VF-safe)
        closed_cubics: int = 8,  # target after refit
        max_open_cubics: int = 16,
    ) -> None:
        self.fit_budget = float(fit_budget)
        self.min_step = float(min_step)
        self.corner_deg = float(corner_deg)
        self.short_du = float(short_du)
        self.sliver_area = float(sliver_area)
        self.closed_cubics = int(closed_cubics)
        self.max_open_cubics = int(max_open_cubics)


_DEFAULT = TidyParams()


def _seg_len(seg: object) -> float:
    if isinstance(seg, LineSegment):
        return math.hypot(seg.p1.x - seg.p0.x, seg.p1.y - seg.p0.y)
    if isinstance(seg, CubicSegment):
        return math.hypot(seg.p3.x - seg.p0.x, seg.p3.y - seg.p0.y)
    return 0.0


def merge_short_segments(contour: Contour, *, short_du: float = 1.5) -> Contour:
    """Drop near-zero chord segments; keep at least a triangle when closed."""
    segs = list(contour.segments)
    if len(segs) < 2:
        return contour
    kept: list[object] = []
    for seg in segs:
        if _seg_len(seg) < short_du and kept:
            prev = kept[-1]
            if isinstance(prev, LineSegment) and isinstance(seg, LineSegment):
                kept[-1] = LineSegment(prev.p0, seg.p1)
                continue
            if isinstance(prev, CubicSegment) and isinstance(seg, (LineSegment, CubicSegment)):
                end = seg.p1 if isinstance(seg, LineSegment) else seg.p3
                kept[-1] = CubicSegment(prev.p0, prev.p1, prev.p2, end)
                continue
        kept.append(seg)
    min_keep = 3 if contour.closed else 1
    if len(kept) < min_keep:
        return contour
    return Contour(tuple(kept), closed=contour.closed)  # type: ignore[arg-type]


def _resample_closed(pts: Sequence[tuple[float, float]], n: int) -> list[tuple[float, float]]:
    if n < 3 or len(pts) < 3:
        return list(pts)
    ring = list(pts)
    if math.hypot(ring[0][0] - ring[-1][0], ring[0][1] - ring[-1][1]) < 1e-6:
        ring = ring[:-1]
    if len(ring) < 3:
        return ring
    loop = ring + [ring[0]]
    edges = [
        math.hypot(loop[i + 1][0] - loop[i][0], loop[i + 1][1] - loop[i][1])
        for i in range(len(loop) - 1)
    ]
    total = sum(edges)
    if total <= 0:
        return ring
    samples: list[tuple[float, float]] = []
    for k in range(n):
        target = total * k / n
        acc = 0.0
        for i, step in enumerate(edges):
            if acc + step >= target - 1e-9:
                t = 0.0 if step == 0 else (target - acc) / step
                a, b = loop[i], loop[i + 1]
                samples.append((a[0] + t * (b[0] - a[0]), a[1] + t * (b[1] - a[1])))
                break
            acc += step
        else:
            samples.append(ring[0])
    return samples


def fixed_closed_cubic_refit(contour: Contour, n_cubics: int = 8) -> Contour:
    """Equal-arc resample → exactly ``n_cubics`` G1 cubics (VF-stable)."""
    if n_cubics < 3:
        raise ValueError(f"n_cubics must be ≥ 3, got {n_cubics}")
    pts = _contour_sample_polyline(contour, min_step=1.0)
    samples = _resample_closed(pts, n_cubics)
    if len(samples) < n_cubics:
        return contour
    segs: list[CubicSegment] = []
    for i in range(n_cubics):
        p0 = samples[i]
        p3 = samples[(i + 1) % n_cubics]
        prev_p = samples[(i - 1) % n_cubics]
        next_p = samples[(i + 2) % n_cubics]
        # Unit tangents from neighboring samples (G1 across joins).
        t_in = (p3[0] - prev_p[0], p3[1] - prev_p[1])
        t_out = (next_p[0] - p0[0], next_p[1] - p0[1])
        n_in = math.hypot(*t_in) or 1.0
        n_out = math.hypot(*t_out) or 1.0
        t_in = (t_in[0] / n_in, t_in[1] / n_in)
        t_out = (t_out[0] / n_out, t_out[1] / n_out)
        chord = math.hypot(p3[0] - p0[0], p3[1] - p0[1])
        h = chord / 3.0
        c1 = (p0[0] + t_in[0] * h, p0[1] + t_in[1] * h)
        c2 = (p3[0] - t_out[0] * h, p3[1] - t_out[1] * h)
        segs.append(CubicSegment(Point(*p0), Point(*c1), Point(*c2), Point(*p3)))
    fitted = Contour(tuple(segs), closed=True)
    if signed_area(contour) * signed_area(fitted) < 0:
        fitted = reverse_contour(fitted)
    return fitted


def tidy_outline(outline: Outline, params: TidyParams | None = None) -> Outline:
    """Refit + merge shorts + drop slivers. Closed contours get fixed cubics."""
    p = params or _DEFAULT
    pre = Outline(
        tuple(merge_short_segments(c, short_du=p.short_du) for c in outline.contours)
    )
    kept: list[Contour] = []
    open_need_adaptive: list[Contour] = []
    open_indices: list[int] = []

    closed = [c for c in pre.contours if c.closed]
    designed = bool(closed) and all(len(c.segments) in (3, 4, 6) for c in closed)

    for c in pre.contours:
        if c.closed:
            if designed or len(c.segments) <= 4:
                kept.append(merge_short_segments(c, short_du=p.short_du))
            elif len(c.segments) != p.closed_cubics:
                fitted = fixed_closed_cubic_refit(c, p.closed_cubics)
                kept.append(merge_short_segments(fitted, short_du=p.short_du))
            else:
                kept.append(merge_short_segments(c, short_du=p.short_du))
        else:
            open_indices.append(len(kept))
            kept.append(c)
            open_need_adaptive.append(c)

    # Open strokes: merge micro-edges only.
    for idx, src in zip(open_indices, open_need_adaptive, strict=True):
        kept[idx] = merge_short_segments(src, short_du=p.short_du)

    if p.sliver_area <= 0:
        return Outline(tuple(kept))
    final: list[Contour] = []
    for c in kept:
        area = abs(signed_area(c))
        if area < p.sliver_area and len(kept) > 1 and c.closed:
            continue
        final.append(c)
    if not final:
        return Outline(tuple(kept))
    return Outline(tuple(final))


def tidy_drawing(drawing: object, params: TidyParams | None = None) -> object:
    """Tidy a :class:`~typekernel.draw.Drawing`, preserving roles/order/slots.

    Contours are refit in place (same count and order) so VF masters stay
    signature-compatible. Slivers are not dropped here — that would change
    contour counts across weight.
    """
    from typekernel.draw import Drawing

    if not isinstance(drawing, Drawing):
        raise TypeError(f"tidy_drawing expects Drawing, got {type(drawing)!r}")
    p = params or _DEFAULT

    def _needs_refit(contour: Contour) -> bool:
        if not contour.closed:
            return False
        # Only refit clearly bloated expands; keep designed 4–12 cubic rings.
        return len(contour.segments) > max(p.closed_cubics * 2, 16)

    if not any(_needs_refit(c) for c in drawing.contours):
        return drawing

    new_contours = []
    from typekernel.draw.fragment import Node

    new_nodes: list[tuple[Node, ...]] = []
    for contour, nodes in zip(drawing.contours, drawing.nodes, strict=True):
        if _needs_refit(contour):
            fitted = fixed_closed_cubic_refit(contour, p.closed_cubics)
            fitted = merge_short_segments(fitted, short_du=p.short_du)
            new_contours.append(fitted)
            new_nodes.append(())
        else:
            new_contours.append(contour)
            new_nodes.append(nodes)
    return Drawing(
        tuple(new_contours),
        drawing.roles,
        tuple(new_nodes),
        slots=drawing.slots,
        measures=drawing.measures,
    )
