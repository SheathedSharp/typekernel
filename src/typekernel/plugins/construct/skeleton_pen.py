"""Skeleton + pen construct plugin (ARCHITECTURE.md M6 / §3 construct table).

Wraps :mod:`typekernel.geo.stroke` into a :class:`~typekernel.draw.Drawing`.
No letter names — projects supply centerlines; this module only expands pens.
"""

from __future__ import annotations

from collections.abc import Sequence
from typekernel.draw.drawing import ContourRole, Drawing
from typekernel.geo.contour import Contour, reverse_contour, signed_area
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
    "pointed_pen",
    "expand_skeleton",
    "expand_skeleton_cubic",
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


def _normalize_winding(contour: Contour, *, want_positive: bool) -> Contour:
    area = signed_area(contour)
    if area == 0.0:
        return contour
    if (area > 0.0) == want_positive:
        return contour
    return reverse_contour(contour)


def _drawing_from_contours(contours: tuple[Contour, ...]) -> Drawing:
    """Assign ink/counter and normalize winding (outer CCW, hole CW).

    A single expanded stroke is always ``ink``. Rings: largest |area| is ink,
    remaining contours are counters.
    """
    if not contours:
        return Drawing((), (), (), slots=())
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


def expand_skeleton(
    centerline: Centerline | Sequence[tuple[float, float]],
    pen: Pen,
    *,
    join: JoinStyle = "round",
    cap: CapStyle = "round",
    miter_limit: float = 4.0,
) -> Drawing:
    """Expand a polyline skeleton with ``pen`` into a :class:`Drawing`.

    Closed centerlines that yield a ring get ``ink`` + ``counter`` roles from
    winding. Open strokes become a single ``ink`` contour.
    """
    outline = expand(
        centerline,
        pen,
        join=join,
        cap=cap,
        miter_limit=miter_limit,
    )
    return _drawing_from_contours(outline.contours)


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
    return _drawing_from_contours(outline.contours), report
