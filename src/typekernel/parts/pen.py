"""DesignContext helpers for midline pen expand.

Thin wrappers around :mod:`typekernel.geo.stroke`. Construction only — not a
weight axis. Glyph-skeleton recipes (``trace_letter``) are intentionally absent
until the general expand layer is locked by synthetic fixtures.
"""

from __future__ import annotations

from collections.abc import Sequence

from typekernel.geo.outline import Outline
from typekernel.geo.stroke import CapStyle, Centerline, JoinStyle, Pen, expand
from typekernel.parts.context import DesignContext

__all__ = [
    "CapStyle",
    "Centerline",
    "JoinStyle",
    "Pen",
    "expand",
    "expand_polyline",
    "pen_from_context",
]


def pen_from_context(
    ctx: DesignContext,
    *,
    thickness: float | None = None,
    contrast: float | None = None,
    angle_deg: float = 0.0,
) -> Pen:
    """Build a :class:`~typekernel.geo.stroke.Pen` from family rhythm."""
    return Pen(
        thickness=ctx.stem if thickness is None else thickness,
        contrast=ctx.contrast if contrast is None else contrast,
        angle_deg=angle_deg,
    )


def expand_polyline(
    points: Sequence[tuple[float, float]] | Centerline,
    ctx: DesignContext,
    *,
    thickness: float | None = None,
    contrast: float | None = None,
    angle_deg: float = 0.0,
    join: JoinStyle = "miter",
    cap: CapStyle = "butt",
    miter_limit: float = 4.0,
    closed: bool = False,
) -> Outline:
    """Expand a polyline centerline with a context-derived contrast pen."""
    pen = pen_from_context(
        ctx, thickness=thickness, contrast=contrast, angle_deg=angle_deg
    )
    if isinstance(points, Centerline):
        cl = points
    else:
        cl = Centerline.from_points(points, closed=closed)
    return expand(cl, pen, join=join, cap=cap, miter_limit=miter_limit)
