"""Aperture / counter-opening operators.

General cuts that open a bowl or ring on a chosen side. Synthetic-fixture
first; not glyph recipes. Boolean steps need ``typekernel[boolean]`` (pathops).
"""

from __future__ import annotations

from typing import Literal

from typekernel.geo.boolean import boolean_op
from typekernel.geo.outline import Outline, bounds
from typekernel.geo.path_builder import PathBuilder
from typekernel.parts.context import DesignContext

Side = Literal["left", "right", "top", "bottom"]


def aperture_bite(
    ctx: DesignContext,
    *,
    side: Side,
    center: tuple[float, float],
    width: float,
    height: float,
    depth: float | None = None,
    radius: float | None = None,
) -> Outline:
    """Build the cutting piece used to open an aperture on ``side``.

    ``center`` is the bowl/ring center. The bite sits on the named side and
    extends ``depth`` past the outer edge (default ``ctx.stem``).
    """
    if width <= 0 or height <= 0:
        raise ValueError("width and height must be positive")
    cx, cy = center
    d = ctx.stem if depth is None else depth
    if d <= 0:
        raise ValueError(f"depth must be positive, got {d!r}")
    r = (ctx.join_radius * 0.35) if radius is None else radius
    # Estimate outer extent from width/height args relative to center —
    # callers usually pass absolute bite box via open_counter.
    if side == "right":
        x0, x1 = cx, cx + width + d
        y0, y1 = cy - height / 2.0, cy + height / 2.0
    elif side == "left":
        x0, x1 = cx - width - d, cx
        y0, y1 = cy - height / 2.0, cy + height / 2.0
    elif side == "top":
        x0, x1 = cx - width / 2.0, cx + width / 2.0
        y0, y1 = cy, cy + height + d
    elif side == "bottom":
        x0, x1 = cx - width / 2.0, cx + width / 2.0
        y0, y1 = cy - height - d, cy
    else:
        raise ValueError(f"unknown side: {side!r}")
    return _rounded_rect(x0, y0, x1, y1, max(0.0, r))


def open_counter(
    outline: Outline,
    side: Side,
    amount: float,
    ctx: DesignContext,
    *,
    height_ratio: float | None = None,
    radius: float | None = None,
) -> Outline:
    """Open an aperture in ``outline`` on ``side`` by boolean-differencing a bite.

    ``amount`` is the opening width as a fraction of the outline's half-extent
    on that axis when in ``(0, 1]``, or an absolute design-unit width when
    ``> 1``. ``height_ratio`` (default derived from ``ctx.aperture``) scales the
    opening height vs the outline's span on the perpendicular axis.

    Works on solid bowls, rings (outer+hole contours), or any closed outline.
    """
    if amount <= 0:
        raise ValueError(f"amount must be positive, got {amount!r}")
    try:
        min_x, min_y, max_x, max_y = bounds(outline)
    except ValueError:
        return outline
    w = max_x - min_x
    h = max_y - min_y
    cx, cy = (min_x + max_x) / 2.0, (min_y + max_y) / 2.0
    hr = (0.35 + 0.25 * ctx.aperture) if height_ratio is None else height_ratio
    if hr <= 0 or hr > 1.5:
        raise ValueError(f"height_ratio out of range: {hr!r}")

    if amount <= 1.0:
        gap_w = amount * (w / 2.0)
    else:
        gap_w = amount
    gap_h = h * hr
    depth = max(ctx.stem, gap_w * 0.15)

    if side == "right":
        x0, x1 = max_x - gap_w, max_x + depth
        y0, y1 = cy - gap_h / 2.0, cy + gap_h / 2.0
    elif side == "left":
        x0, x1 = min_x - depth, min_x + gap_w
        y0, y1 = cy - gap_h / 2.0, cy + gap_h / 2.0
    elif side == "top":
        # amount is vertical opening depth from top
        gap_v = amount * (h / 2.0) if amount <= 1.0 else amount
        gap_w = w * hr
        x0, x1 = cx - gap_w / 2.0, cx + gap_w / 2.0
        y0, y1 = max_y - gap_v, max_y + depth
    elif side == "bottom":
        gap_v = amount * (h / 2.0) if amount <= 1.0 else amount
        gap_w = w * hr
        x0, x1 = cx - gap_w / 2.0, cx + gap_w / 2.0
        y0, y1 = min_y - depth, min_y + gap_v
    else:
        raise ValueError(f"unknown side: {side!r}")

    r = (ctx.join_radius * 0.3) if radius is None else radius
    bite = _rounded_rect(x0, y0, x1, y1, max(0.0, r))
    return boolean_op(outline, bite, "difference")


def open_bowl_ring(
    outer: Outline,
    hole: Outline,
    side: Side,
    amount: float,
    ctx: DesignContext,
    *,
    height_ratio: float | None = None,
    radius: float | None = None,
) -> Outline:
    """Subtract ``hole`` from ``outer``, then :func:`open_counter` on ``side``."""
    ring = boolean_op(outer, hole, "difference")
    return open_counter(
        ring, side, amount, ctx, height_ratio=height_ratio, radius=radius
    )


def _rounded_rect(x0: float, y0: float, x1: float, y1: float, radius: float) -> Outline:
    from typekernel.geo.path_helpers import KAPPA

    if x1 < x0:
        x0, x1 = x1, x0
    if y1 < y0:
        y0, y1 = y1, y0
    r = min(radius, abs(x1 - x0) / 2.0, abs(y1 - y0) / 2.0)
    b = PathBuilder()
    if r <= 0:
        b.moveTo(x0, y0)
        b.lineTo(x1, y0)
        b.lineTo(x1, y1)
        b.lineTo(x0, y1)
        b.closePath()
        return b.build()
    b.moveTo(x0 + r, y0)
    b.lineTo(x1 - r, y0)
    b.curveTo(x1 - r + r * KAPPA, y0, x1, y0 + r - r * KAPPA, x1, y0 + r)
    b.lineTo(x1, y1 - r)
    b.curveTo(x1, y1 - r + r * KAPPA, x1 - r + r * KAPPA, y1, x1 - r, y1)
    b.lineTo(x0 + r, y1)
    b.curveTo(x0 + r - r * KAPPA, y1, x0, y1 - r + r * KAPPA, x0, y1 - r)
    b.lineTo(x0, y0 + r)
    b.curveTo(x0, y0 + r - r * KAPPA, x0 + r - r * KAPPA, y0, x0 + r, y0)
    b.closePath()
    return b.build()
