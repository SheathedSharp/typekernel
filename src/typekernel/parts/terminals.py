"""Terminal operators — shear, flat, flare, ball, and hook ends.

General outline operators for stroke endings. Synthetic-fixture first; not
glyph-specific beauty. Boolean steps need ``typekernel[boolean]`` (pathops).
"""

from __future__ import annotations

import math
from collections.abc import Callable
from typing import Literal

from typekernel.geo.boolean import boolean_op
from typekernel.geo.contour import Contour
from typekernel.geo.outline import Outline, bounds
from typekernel.geo.path_builder import PathBuilder
from typekernel.geo.point import Point
from typekernel.geo.segment import CubicSegment, LineSegment
from typekernel.parts.context import DesignContext

Side = Literal["left", "right", "top", "bottom"]


def shear_end(
    outline: Outline,
    at: tuple[float, float],
    angle_deg: float,
    *,
    band: float | None = None,
    along: Literal["x", "y"] = "y",
    inward: Literal["auto", "+", "-"] = "auto",
) -> Outline:
    """Shear the terminal band at ``at`` by ``angle_deg`` (designed deltas).

    Inside a band of thickness ``band`` starting at the end ``at``, points are
    shifted so the end receives full shear and the inner edge of the band
    receives none (smooth falloff). For ``along="y"`` (horizontal end)::

        falloff = max(0, band - |y - at_y|)   # toward the inward side only
        x\' = x + falloff * tan(angle)

    ``inward`` selects which side of ``at`` holds the stem (``auto`` picks the
    side with more outline extent). ``angle_deg`` 0 is a no-op. Not stroke expand.
    """
    ax, ay = at
    try:
        min_x, min_y, max_x, max_y = bounds(outline)
    except ValueError:
        return outline
    if band is None:
        band = max(8.0, 0.15 * max(max_x - min_x, max_y - min_y))
    if band <= 0:
        raise ValueError(f"band must be positive, got {band!r}")
    k = math.tan(math.radians(angle_deg))
    if abs(k) < 1e-15:
        return outline

    if along == "y":
        if inward == "auto":
            inward_sign = 1.0 if (max_y - ay) >= (ay - min_y) else -1.0
        else:
            inward_sign = 1.0 if inward == "+" else -1.0

        def map_pt(p: Point) -> Point:
            # Distance from end along inward direction
            dist = (p.y - ay) * inward_sign
            if 0.0 <= dist <= band:
                falloff = band - dist
                return Point(p.x + falloff * k, p.y)
            return p

    else:
        if inward == "auto":
            inward_sign = 1.0 if (max_x - ax) >= (ax - min_x) else -1.0
        else:
            inward_sign = 1.0 if inward == "+" else -1.0

        def map_pt(p: Point) -> Point:
            dist = (p.x - ax) * inward_sign
            if 0.0 <= dist <= band:
                falloff = band - dist
                return Point(p.x, p.y + falloff * k)
            return p

    return _map_points(outline, map_pt)


def flare_end(
    outline: Outline,
    at: tuple[float, float],
    *,
    amount: float = 0.4,
    band: float | None = None,
    along: Literal["x", "y"] = "y",
    inward: Literal["auto", "+", "-"] = "auto",
) -> Outline:
    """Widen the terminal band so the stroke flares toward ``at``.

    Unlike :func:`shear_end` (which skews the tip), this expands points away
    from the local cross-axis centreline inside ``band``, peaking at ``at``.
    ``amount`` is tip half-width gain as a fraction of the outline's half-span
    on the cross axis (``0`` = no-op; ``0.4`` ≈ 40% wider at the tip).

    Designed for open stroke ends (``c``/``e``/``r``/``s`` tips, arm ends).
    Not stroke-expand weight.
    """
    if amount == 0.0:
        return outline
    if amount < 0:
        raise ValueError(f"amount must be >= 0, got {amount!r}")
    ax, ay = at
    try:
        min_x, min_y, max_x, max_y = bounds(outline)
    except ValueError:
        return outline
    if band is None:
        band = max(8.0, 0.4 * max(max_x - min_x, max_y - min_y))
    if band <= 0:
        raise ValueError(f"band must be positive, got {band!r}")

    if along == "y":
        half = max((max_x - min_x) / 2.0, 1e-6)
        cx = 0.5 * (min_x + max_x)
        if inward == "auto":
            inward_sign = 1.0 if (max_y - ay) >= (ay - min_y) else -1.0
        else:
            inward_sign = 1.0 if inward == "+" else -1.0

        def map_pt(p: Point) -> Point:
            dist = (p.y - ay) * inward_sign
            if 0.0 <= dist <= band:
                falloff = (band - dist) / band
                # Push away from centreline; points on centreline stay put.
                side = p.x - cx
                gain = amount * half * falloff
                if abs(side) < 1e-9:
                    return p
                return Point(p.x + (1.0 if side > 0 else -1.0) * gain, p.y)
            return p

    else:
        half = max((max_y - min_y) / 2.0, 1e-6)
        cy = 0.5 * (min_y + max_y)
        if inward == "auto":
            inward_sign = 1.0 if (max_x - ax) >= (ax - min_x) else -1.0
        else:
            inward_sign = 1.0 if inward == "+" else -1.0

        def map_pt(p: Point) -> Point:
            dist = (p.x - ax) * inward_sign
            if 0.0 <= dist <= band:
                falloff = (band - dist) / band
                side = p.y - cy
                gain = amount * half * falloff
                if abs(side) < 1e-9:
                    return p
                return Point(p.x, p.y + (1.0 if side > 0 else -1.0) * gain)
            return p

    return _map_points(outline, map_pt)


def flat_end(
    outline: Outline,
    at: tuple[float, float],
    *,
    angle_deg: float = 0.0,
    length: float = 400.0,
    kerf: float = 2.0,
    keep: Literal["positive", "negative"] = "positive",
) -> Outline:
    """Cut a flat terminal through ``at`` with a thin knife (boolean difference).

    The knife is a parallelogram centered on ``at``, length ``length`` along the
    cut, thickness ``kerf``, oriented at ``angle_deg`` from +x (0° = horizontal
    cut). ``keep`` selects which half-plane of material remains after the cut
    relative to the knife normal (positive = toward the normal of the cut
    direction rotated +90°).
    """
    if length <= 0 or kerf <= 0:
        raise ValueError("length and kerf must be positive")
    ax, ay = at
    rad = math.radians(angle_deg)
    tx, ty = math.cos(rad), math.sin(rad)  # along cut
    nx, ny = -ty, tx  # normal
    half_l = length / 2.0
    half_k = kerf / 2.0
    # Knife parallelogram around the cut line
    corners = [
        (ax - tx * half_l - nx * half_k, ay - ty * half_l - ny * half_k),
        (ax + tx * half_l - nx * half_k, ay + ty * half_l - ny * half_k),
        (ax + tx * half_l + nx * half_k, ay + ty * half_l + ny * half_k),
        (ax - tx * half_l + nx * half_k, ay - ty * half_l + ny * half_k),
    ]
    knife = _poly(corners)
    # Large half-plane discard on one side of the cut
    try:
        min_x, min_y, max_x, max_y = bounds(outline)
    except ValueError:
        return outline
    diag = math.hypot(max_x - min_x, max_y - min_y) + length + 50.0
    sign = 1.0 if keep == "positive" else -1.0
    # Discard region: from knife centerline outward along ±normal
    discard = _poly(
        [
            (ax - tx * diag + nx * sign * half_k, ay - ty * diag + ny * sign * half_k),
            (ax + tx * diag + nx * sign * half_k, ay + ty * diag + ny * sign * half_k),
            (ax + tx * diag + nx * sign * diag, ay + ty * diag + ny * sign * diag),
            (ax - tx * diag + nx * sign * diag, ay - ty * diag + ny * sign * diag),
        ]
    )
    cut = boolean_op(outline, knife, "difference")
    return boolean_op(cut, discard, "difference")


def ball_end(
    outline: Outline,
    at: tuple[float, float],
    *,
    radius: float,
    ctx: DesignContext | None = None,
) -> Outline:
    """Union a circular ball terminal at ``at`` onto ``outline``."""
    del ctx
    if radius <= 0:
        raise ValueError(f"radius must be positive, got {radius!r}")
    ax, ay = at
    ball = _ellipse(ax, ay, radius, radius)
    return boolean_op(outline, ball, "union")


def hook_end(
    outline: Outline,
    at: tuple[float, float],
    *,
    radius: float,
    width: float,
    sweep_deg: float = 180.0,
    start_deg: float = 180.0,
    ctx: DesignContext | None = None,
) -> Outline:
    """Union a curved hook terminal (annular sector stroke) at ``at``.

    The hook is an open annular arc of outer radius ``radius``, thickness
    ``width``, sweeping ``sweep_deg`` from ``start_deg`` (CCW from +x).
    """
    del ctx
    if radius <= 0 or width <= 0:
        raise ValueError("radius and width must be positive")
    if width >= radius:
        raise ValueError("width must be < radius for a hollow hook")
    inner_r = radius - width
    ax, ay = at
    outer = _arc_ring_sector(ax, ay, radius, inner_r, start_deg, start_deg + sweep_deg)
    return boolean_op(outline, outer, "union")


def ball_terminal_piece(
    ctx: DesignContext,
    cx: float,
    cy: float,
    *,
    radius: float | None = None,
) -> Outline:
    """Standalone ball piece (same geometry as :func:`ball_end`'s tip)."""
    r = ctx.stem * 0.55 if radius is None else radius
    return _ellipse(cx, cy, r, r)


def flat_terminal_piece(
    ctx: DesignContext,
    x0: float,
    y0: float,
    x1: float,
    y1: float,
    *,
    shear: float = 0.0,
) -> Outline:
    """Standalone flat / sheared rectangular terminal piece."""
    t = abs(y1 - y0) if abs(y1 - y0) > 1e-9 else ctx.stem
    s = shear * t
    return _poly([(x0 + s, y0), (x1 + s, y0), (x1 - s, y1), (x0 - s, y1)])


def flared_terminal_piece(
    ctx: DesignContext,
    x0: float,
    y0: float,
    x1: float,
    y1: float,
    *,
    flare: float = 0.4,
) -> Outline:
    """Standalone flared trapezoid terminal (wider at the outer end).

    ``(x0, y0)``–``(x1, y0)`` is the stem-facing face; ``y1`` is the outer tip.
    ``flare`` widens the tip face relative to ``|x1 - x0|``. Agents union this
    onto a stem tip, or prefer :func:`flare_end` to reshape an existing outline.
    """
    w = abs(x1 - x0) if abs(x1 - x0) > 1e-9 else ctx.stem
    tip_half = 0.5 * w * (1.0 + flare)
    stem_half = 0.5 * w
    cx = 0.5 * (x0 + x1)
    return _poly(
        [
            (cx - stem_half, y0),
            (cx + stem_half, y0),
            (cx + tip_half, y1),
            (cx - tip_half, y1),
        ]
    )


def hook_terminal_piece(
    ctx: DesignContext,
    cx: float,
    cy: float,
    *,
    radius: float | None = None,
    width: float | None = None,
    sweep_deg: float = 180.0,
    start_deg: float = 180.0,
) -> Outline:
    """Standalone hook piece for agents to union manually."""
    r = (ctx.stem * 1.8) if radius is None else radius
    w = ctx.stem if width is None else width
    return _arc_ring_sector(cx, cy, r, max(r - w, 1.0), start_deg, start_deg + sweep_deg)


# --- helpers ----------------------------------------------------------------


def _map_points(outline: Outline, mapper: Callable[[Point], Point]) -> Outline:
    contours: list[Contour] = []
    for c in outline.contours:
        segs: list[LineSegment | CubicSegment] = []
        for seg in c.segments:
            pts = [mapper(p) for p in seg.points]
            if isinstance(seg, LineSegment):
                segs.append(LineSegment(pts[0], pts[1]))
            else:
                segs.append(CubicSegment(pts[0], pts[1], pts[2], pts[3]))
        contours.append(Contour(tuple(segs), closed=c.closed))
    return Outline(tuple(contours))


def _poly(corners: list[tuple[float, float]]) -> Outline:
    b = PathBuilder()
    b.moveTo(*corners[0])
    for pt in corners[1:]:
        b.lineTo(*pt)
    b.closePath()
    return b.build()


def _ellipse(cx: float, cy: float, rx: float, ry: float) -> Outline:
    b = PathBuilder()
    b.addEllipse(cx, cy, rx, ry)
    return b.build()


def _arc_ring_sector(
    cx: float,
    cy: float,
    outer_r: float,
    inner_r: float,
    start_deg: float,
    end_deg: float,
) -> Outline:
    """Closed annular sector as outer arc → radial → inner arc reverse → radial."""
    b = PathBuilder()
    # Start at outer start angle
    a0 = math.radians(start_deg)
    a1 = math.radians(end_deg)
    ox0, oy0 = cx + outer_r * math.cos(a0), cy + outer_r * math.sin(a0)
    b.moveTo(ox0, oy0)
    b.arcTo(cx, cy, outer_r, outer_r, end_deg, start_angle_deg=start_deg)
    ix1, iy1 = cx + inner_r * math.cos(a1), cy + inner_r * math.sin(a1)
    b.lineTo(ix1, iy1)
    b.arcTo(cx, cy, inner_r, inner_r, start_deg, start_angle_deg=end_deg)
    b.closePath()
    return b.build()
