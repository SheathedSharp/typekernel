"""Shared primitives for letter-writing / calligraphy script faces.

Brand glyph skeletons stay in examples. This module is the reusable geometry,
nib-stroke, writing-rail, and join-polish layer that examples call before /
after :func:`~typekernel.parts.skeleton.trace_letter`.

Slant is a **coordinate shear** baked into centerlines — not
:func:`~typekernel.parts.italic.slant_composed_glyph` / oblique post-process.
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass

from typekernel.geo.stroke import CapStyle, CubicBezier, JoinStyle
from typekernel.parts.compose import ComposedGlyph
from typekernel.parts.context import DesignContext
from typekernel.parts.skeleton import Skeleton, Stroke, trace_letter

__all__ = [
    "K_CIRCLE",
    "NibSpec",
    "chaikin_subdivide",
    "ellipse_cubics",
    "entry_rail",
    "exit_rail",
    "nib_ellipse_stroke",
    "nib_polyline_stroke",
    "polish_script_joins",
    "shear_xy",
    "slant_shear",
    "trace_nib_strokes",
]

# Cubic approximation constant for unit circle quarters.
K_CIRCLE: float = 0.5523


@dataclass(frozen=True, slots=True)
class NibSpec:
    """Contrast broad-nib defaults for script stroke expansion."""

    thickness: float
    contrast: float
    angle_deg: float
    join: JoinStyle = "round"
    cap: CapStyle = "round"
    chaikin_rounds: int = 4


def slant_shear(degrees: float) -> float:
    """Horizontal shear factor ``tan(radians(degrees))`` for writing slant."""
    return math.tan(math.radians(degrees))


def shear_xy(x: float, y: float, shear: float) -> tuple[float, float]:
    """Apply writing slant: ``(x + y * shear, y)``."""
    return (x + y * shear, y)


def chaikin_subdivide(
    pts: Sequence[tuple[float, float]], rounds: int = 4
) -> list[tuple[float, float]]:
    """Corner-cutting densify for polyline skeletons (open polylines).

    Endpoints are preserved. ``rounds=0`` returns a copy of ``pts``.
    """
    if rounds < 0:
        raise ValueError("rounds must be >= 0")
    cur: list[tuple[float, float]] = [(float(p[0]), float(p[1])) for p in pts]
    if len(cur) < 2:
        return cur
    for _ in range(rounds):
        nxt: list[tuple[float, float]] = [cur[0]]
        for i in range(len(cur) - 1):
            a, b = cur[i], cur[i + 1]
            nxt.append((0.75 * a[0] + 0.25 * b[0], 0.75 * a[1] + 0.25 * b[1]))
            nxt.append((0.25 * a[0] + 0.75 * b[0], 0.25 * a[1] + 0.75 * b[1]))
        nxt.append(cur[-1])
        cur = nxt
    return cur


def entry_rail(
    x0: float,
    x1: float,
    *,
    y: float,
    lift: float,
    dip: float = 6.0,
    start_rise: float = 20.0,
) -> list[tuple[float, float]]:
    """Three-point entry approach into a letter (pre-shear coordinates)."""
    mid = (x0 + x1) / 2.0
    return [(x0, y + start_rise), (mid, y - dip), (x1, lift)]


def exit_rail(
    x0: float,
    x1: float,
    *,
    y: float,
    lift: float,
    dip: float = 6.0,
    end_rise: float = 28.0,
) -> list[tuple[float, float]]:
    """Three-point exit departure from a letter (pre-shear coordinates)."""
    mid = (x0 + x1) / 2.0
    return [(x0, lift * 0.5), (mid, y - dip), (x1, y + end_rise)]


def ellipse_cubics(
    cx: float,
    cy: float,
    rx: float,
    ry: float,
    *,
    shear: float = 0.0,
    k: float = K_CIRCLE,
) -> tuple[CubicBezier, CubicBezier, CubicBezier, CubicBezier]:
    """Four-cubic ellipse in pre-shear coords, then optional writing shear."""

    def S(x: float, y: float) -> tuple[float, float]:
        return shear_xy(x, y, shear)

    return (
        CubicBezier(
            S(cx + rx, cy),
            S(cx + rx, cy + k * ry),
            S(cx + k * rx, cy + ry),
            S(cx, cy + ry),
        ),
        CubicBezier(
            S(cx, cy + ry),
            S(cx - k * rx, cy + ry),
            S(cx - rx, cy + k * ry),
            S(cx - rx, cy),
        ),
        CubicBezier(
            S(cx - rx, cy),
            S(cx - rx, cy - k * ry),
            S(cx - k * rx, cy - ry),
            S(cx, cy - ry),
        ),
        CubicBezier(
            S(cx, cy - ry),
            S(cx + k * rx, cy - ry),
            S(cx + rx, cy - k * ry),
            S(cx + rx, cy),
        ),
    )


def nib_polyline_stroke(
    name: str,
    pts: Sequence[tuple[float, float]],
    nib: NibSpec,
    *,
    shear: float = 0.0,
    thickness: float | None = None,
    contrast: float | None = None,
    smooth: int | None = None,
) -> Stroke:
    """Chaikin-densify + shear polyline into a contrast-nib :class:`Stroke`."""
    rounds = nib.chaikin_rounds if smooth is None else smooth
    dense = chaikin_subdivide(pts, rounds=rounds)
    sheared = [shear_xy(p[0], p[1], shear) for p in dense]
    return Stroke.from_points(
        name,
        sheared,
        thickness=nib.thickness if thickness is None else thickness,
        contrast=nib.contrast if contrast is None else contrast,
        angle_deg=nib.angle_deg,
        join=nib.join,
        cap=nib.cap,
    )


def nib_ellipse_stroke(
    name: str,
    cx: float,
    cy: float,
    rx: float,
    ry: float,
    nib: NibSpec,
    *,
    shear: float = 0.0,
    thickness: float | None = None,
) -> Stroke:
    """Closed elliptical ring stroke under the nib."""
    return Stroke.from_beziers(
        name,
        ellipse_cubics(cx, cy, rx, ry, shear=shear),
        closed=True,
        thickness=nib.thickness if thickness is None else thickness,
        contrast=nib.contrast,
        angle_deg=nib.angle_deg,
        join=nib.join,
        cap=nib.cap,
    )


def polish_script_joins(
    glyph: ComposedGlyph,
    *,
    radius: float | None = None,
    kink_max_deg: float = 42.0,
    ease_curvature: bool = True,
) -> ComposedGlyph:
    """Post-trace join polish for calligraphy unions (explicit, not silent simplify).

    Wraps :func:`~typekernel.optics.glyph_polish.polish_glyph` with a slightly
    wider kink band so round-nib crotches clean up without destroying extrema.
    """
    from typekernel.optics.glyph_polish import GlyphPolishOptions, polish_glyph

    return polish_glyph(
        glyph,
        GlyphPolishOptions(
            joins_policy="tangent_fix",
            tangent_radius=radius,
            kink_max_deg=kink_max_deg,
            ease_curvature=ease_curvature,
        ),
    )


def trace_nib_strokes(
    strokes: Sequence[Stroke],
    ctx: DesignContext,
    *,
    min_contour_area: float = 350.0,
    blend: bool = True,
    heal: bool = True,
    union: bool = True,
    polish_joins: bool = True,
) -> ComposedGlyph:
    """Expand script strokes via library :func:`trace_letter` (heal/strip/refit).

    When ``polish_joins`` is true (default), applies :func:`polish_script_joins`
    after expand — reusable connect/join post-process for script faces.
    """
    glyph = trace_letter(
        Skeleton.of(*strokes),
        ctx,
        union=union,
        blend=blend,
        ease=False,
        join="round",
        cap="round",
        heal=heal,
        min_contour_area=min_contour_area,
    )
    if polish_joins:
        return polish_script_joins(glyph)
    return glyph
