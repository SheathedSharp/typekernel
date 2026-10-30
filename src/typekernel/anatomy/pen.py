"""Pen construction helpers for italic / script starters (target §4.5).

Duplicated tools from ``latin_humanist_italic`` and ``latin_chancery`` live here.
The public stroke API takes a **cubic** skeleton (:class:`~typekernel.geo.stroke.CubicCenterline`
or :class:`~typekernel.draw.Fragment`) and expands with curve-aware offset
(:func:`~typekernel.plugins.construct.expand_skeleton_cubic`).

Polyline point lists are **not** accepted by :func:`stroke`. Project shims may
fit points with :func:`slanted_cubic_from_points`. :func:`expand_slanted_centerline`
remains an internal polyline expand used only as a fallback; both paths run
compile-time :func:`~typekernel.geo.tidy.tidy_drawing` (not heal/blend/seal).
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from typing import Literal, TypeAlias

from typekernel.draw import Drawing, Fragment, Writer, hook, tensioned_arc
from typekernel.geo.point import Point
from typekernel.geo.segment import CubicSegment, LineSegment
from typekernel.geo.stroke import (
    Centerline,
    CubicBezier,
    CubicCenterline,
    Pen,
    polyline_to_cubic_centerline,
)
from typekernel.plugins.construct import broad_nib, expand_skeleton, expand_skeleton_cubic
from typekernel.system import System

__all__ = [
    "assemble",
    "bowl",
    "expand_slanted_centerline",
    "flourish_entry",
    "flourish_exit",
    "fragment_to_cubic_centerline",
    "fuse",
    "nest_bowl",
    "open_arc_cubic",
    "open_arc_points",
    "open_bowl",
    "oval_cubic",
    "oval_points",
    "pen_dot",
    "pen_for_optical_stem",
    "pen_params",
    "project_pen",
    "slanted_centerline",
    "slanted_cubic_from_points",
    "slanted_vertical_optical_ratio",
    "stroke",
    "stroke_fragment",
]

Skeleton: TypeAlias = CubicCenterline | Fragment


def pen_params(system: System) -> tuple[float, float]:
    """Return ``(pen_contrast, pen_angle_deg)`` from System tokens."""
    contrast = float(system.tokens.get("pen_contrast", 0.55))
    angle = float(system.tokens.get("pen_angle_deg", 30.0))
    return contrast, angle


def slanted_vertical_optical_ratio(system: System) -> float:
    """Horizontal stem width per unit pen thickness for a slanted vertical."""
    from typekernel.optics.stem import list_vertical_stems

    contrast, angle = pen_params(system)
    probe_th = 40.0
    cl = slanted_centerline([(200.0, 0.0), (200.0, 500.0)], system, closed=False)
    drawing = expand_skeleton(
        cl,
        broad_nib(probe_th, contrast=contrast, angle_deg=angle),
        join="round",
        cap="round",
    )
    spans = list_vertical_stems(drawing.outline(), y=250.0)
    if not spans or spans[0].width <= 0:
        return 1.0
    return float(spans[0].width) / probe_th


def pen_for_optical_stem(system: System, optical: float) -> Pen:
    """Broad nib whose slanted vertical measures ``optical`` horizontally."""
    contrast, angle = pen_params(system)
    ratio = slanted_vertical_optical_ratio(system)
    thickness = float(optical) / ratio if ratio > 0 else float(optical)
    return broad_nib(thickness, contrast=contrast, angle_deg=angle)


def project_pen(system: System, thickness: float | None = None) -> Pen:
    """Broad nib sized so slanted verticals hit ``thickness`` (default lc stem)."""
    optical = float(system.stem["lc"] if thickness is None else thickness)
    return pen_for_optical_stem(system, optical)


def slanted_centerline(
    points: Sequence[tuple[float, float]],
    system: System,
    *,
    closed: bool = False,
) -> Centerline:
    """Apply ``System.map_xy`` to upright points → polyline :class:`Centerline`."""
    slanted = [system.map_xy(x, y) for x, y in points]
    return Centerline.from_points(slanted, closed=closed)


def slanted_cubic_from_points(
    points: Sequence[tuple[float, float]],
    system: System,
    *,
    closed: bool = False,
) -> CubicCenterline:
    """Fit upright polyline samples to a slanted cubic skeleton."""
    slanted = [system.map_xy(x, y) for x, y in points]
    return polyline_to_cubic_centerline(slanted, closed=closed)


def _xy(p: Point | tuple[float, float]) -> tuple[float, float]:
    if isinstance(p, tuple):
        return (float(p[0]), float(p[1]))
    return (float(p.x), float(p.y))


def fragment_to_cubic_centerline(fragment: Fragment) -> CubicCenterline:
    """Convert a :class:`Fragment` into a cubic centerline (lines → cubics)."""
    beziers: list[CubicBezier] = []
    for seg in fragment.segments:
        if isinstance(seg, LineSegment):
            beziers.append(CubicBezier.line(_xy(seg.p0), _xy(seg.p1)))
        elif isinstance(seg, CubicSegment):
            p0, p1, p2, p3 = seg.points
            beziers.append(CubicBezier(_xy(p0), _xy(p1), _xy(p2), _xy(p3)))
        else:
            pts = list(seg.points)
            if len(pts) < 2:
                continue
            beziers.append(CubicBezier.line(_xy(pts[0]), _xy(pts[-1])))
    if len(beziers) < 1:
        raise ValueError("fragment has no strokeable segments")
    return CubicCenterline(tuple(beziers), closed=False)


def expand_slanted_centerline(
    system: System,
    centerline: Centerline,
    *,
    thickness: float | None = None,
) -> Drawing:
    """Polyline expand (hash-stable path used by migrating starters)."""
    optical = float(system.stem["lc"]) if thickness is None else float(thickness)
    pen = pen_for_optical_stem(system, optical)
    join: Literal["miter", "round", "bevel"] = (
        "bevel" if centerline.closed else "round"
    )
    return expand_skeleton(centerline, pen, join=join, cap="round")


def stroke(
    system: System,
    skeleton: Skeleton,
    *,
    thickness: float | None = None,
) -> Drawing:
    """Expand a **cubic** skeleton with the project broad nib (curve-aware).

    Accepts :class:`CubicCenterline` or :class:`Fragment` only — not polyline
    point lists.
    """
    if isinstance(skeleton, (list, tuple)):
        raise TypeError(
            "anatomy.pen.stroke requires CubicCenterline or Fragment; "
            "got a point sequence. Fit with slanted_cubic_from_points(...) "
            "or call expand_slanted_centerline for the legacy polyline path."
        )
    if isinstance(skeleton, Fragment):
        cubic = fragment_to_cubic_centerline(skeleton)
    elif isinstance(skeleton, CubicCenterline):
        cubic = skeleton
    else:
        raise TypeError(
            f"anatomy.pen.stroke expected CubicCenterline | Fragment, got {type(skeleton)!r}"
        )

    optical = float(system.stem["lc"]) if thickness is None else float(thickness)
    pen = pen_for_optical_stem(system, optical)
    join: Literal["miter", "round", "bevel"] = (
        "bevel" if cubic.closed else "round"
    )
    drawing, _report = expand_skeleton_cubic(cubic, pen, join=join, cap="round")
    from typekernel.geo.tidy import tidy_drawing

    return tidy_drawing(drawing)  # type: ignore[return-value]


def oval_points(
    cx: float,
    cy: float,
    rx: float,
    ry: float,
    *,
    n: int = 64,
) -> list[tuple[float, float]]:
    """Unslanted oval sample points (fixed ``n`` for VF-stable topology)."""
    return [
        (
            cx + rx * math.cos(2.0 * math.pi * i / n),
            cy + ry * math.sin(2.0 * math.pi * i / n),
        )
        for i in range(n)
    ]


def open_arc_points(
    cx: float,
    cy: float,
    rx: float,
    ry: float,
    *,
    start_deg: float,
    end_deg: float,
    n: int = 48,
) -> list[tuple[float, float]]:
    """Unslanted elliptical arc samples (open), degrees CCW from +x."""
    a0 = math.radians(start_deg)
    a1 = math.radians(end_deg)
    return [
        (
            cx + rx * math.cos(a0 + (a1 - a0) * i / (n - 1)),
            cy + ry * math.sin(a0 + (a1 - a0) * i / (n - 1)),
        )
        for i in range(n)
    ]


def oval_cubic(
    system: System,
    *,
    cx: float,
    cy: float,
    rx: float,
    ry: float,
    n: int = 4,
) -> CubicCenterline:
    """Closed oval as a slanted cubic skeleton (κ ellipse, 4 cubics).

    ``n`` is accepted for API compatibility; values other than 4 fall back to
    sampled :func:`oval_points` + fit. Prefer the default four-cubic ellipse.
    """
    if int(n) == 4:
        from typekernel.geo.path_helpers import ellipse_cubics

        segs: list[CubicBezier] = []
        for p0, p1, p2, p3 in ellipse_cubics(cx, cy, rx, ry):

            def _m(pt: object) -> tuple[float, float]:
                return system.map_xy(float(pt.x), float(pt.y))  # type: ignore[attr-defined]

            segs.append(CubicBezier(_m(p0), _m(p1), _m(p2), _m(p3)))
        return CubicCenterline(tuple(segs), closed=True)
    return slanted_cubic_from_points(oval_points(cx, cy, rx, ry, n=n), system, closed=True)


def open_arc_cubic(
    system: System,
    *,
    cx: float,
    cy: float,
    rx: float,
    ry: float,
    start_deg: float,
    end_deg: float,
    n: int = 48,
) -> CubicCenterline:
    """Open elliptical arc as a slanted cubic skeleton."""
    return slanted_cubic_from_points(
        open_arc_points(cx, cy, rx, ry, start_deg=start_deg, end_deg=end_deg, n=n),
        system,
        closed=False,
    )


def bowl(
    system: System,
    *,
    cx: float,
    cy: float,
    rx: float,
    ry: float,
    thickness: float | None = None,
    n: int = 4,
) -> Drawing:
    """Closed oval ring via cubic skeleton + curve-aware expand + tidy."""
    return stroke(system, oval_cubic(system, cx=cx, cy=cy, rx=rx, ry=ry, n=n), thickness=thickness)


def open_bowl(
    system: System,
    *,
    cx: float,
    cy: float,
    rx: float,
    ry: float,
    thickness: float | None = None,
    open_side: str = "right",
    aperture_deg: float = 80.0,
    n: int = 48,
) -> Drawing:
    """Open elliptical bowl; aperture centered on +x (right) or 180° (left)."""
    if open_side not in ("right", "left"):
        raise ValueError(f"open_side must be 'right' or 'left', got {open_side!r}")
    half = float(aperture_deg) / 2.0
    if open_side == "right":
        start_deg, end_deg = half, 360.0 - half
    else:
        start_deg, end_deg = 180.0 + half, 180.0 - half + 360.0
    return stroke(
        system,
        open_arc_cubic(
            system,
            cx=cx,
            cy=cy,
            rx=rx,
            ry=ry,
            start_deg=start_deg,
            end_deg=end_deg,
            n=n,
        ),
        thickness=thickness,
    )


def nest_bowl(
    system: System,
    *,
    stem_x: float,
    side: str,
    width: float,
    xh: float,
    lsb: float = 0.0,
    thickness: float | None = None,
    cy: float | None = None,
    rx: float | None = None,
    ry: float | None = None,
    pull: float = 0.78,
) -> Drawing:
    """Oval bowl nestled against a stem (``side`` left/right of stem)."""
    del lsb  # kept for call-site compatibility with starter signatures
    ov = float(system.overshoot.round)
    rx_v = width * 0.36 if rx is None else float(rx)
    ry_v = (xh / 2.0 + ov * 0.45) if ry is None else float(ry)
    cy_v = (xh / 2.0) if cy is None else float(cy)
    if side == "right":
        cx = stem_x + rx_v * float(pull)
    elif side == "left":
        cx = stem_x - rx_v * float(pull)
    else:
        raise ValueError(f"side must be left/right, got {side!r}")
    return bowl(system, cx=cx, cy=cy_v, rx=rx_v, ry=ry_v, thickness=thickness)


def pen_dot(
    system: System,
    cx: float,
    cy: float,
    *,
    radius: float | None = None,
) -> Drawing:
    """Tittle / period-style **filled** dot, center in pre-slant space."""
    thin = float(system.stem.get("lc_h", system.stem["lc"]))
    if radius is None:
        ref_h = 36.0
        mul = float(system.tokens.get("dot_radius", 28.0)) / ref_h
        r = thin * mul
    else:
        r = float(radius)
    outer = r + thin * 0.5
    n = 48
    pts = [
        system.map_xy(
            cx + outer * math.cos(2.0 * math.pi * i / n),
            cy + outer * math.sin(2.0 * math.pi * i / n),
        )
        for i in range(n)
    ]
    writer = Writer()
    writer.start(pts[0])
    for pt in pts[1:]:
        writer.line(pt)
    writer.close()
    return writer.build()


def flourish_exit(
    system: System,
    stem_edge_x: float,
    y_join: float,
    tip: tuple[float, float],
    *,
    depth: float | None = None,
) -> Fragment:
    """Hook-shaped exit flourish from a stem edge."""
    d = float(system.tokens.get("flourish_depth", 40.0) if depth is None else depth)
    return hook(stem_edge_x, y_join, Point(*tip), depth=d, tension=0.55)


def flourish_entry(
    system: System,
    p0: tuple[float, float],
    p1: tuple[float, float],
    *,
    tension: float = 0.6,
) -> Fragment:
    """Lead-in arc into a stem."""
    del system
    a = Point(*p0)
    b = Point(*p1)
    return tensioned_arc(a, Point(0.35, 1.0), b, Point(0.0, 1.0), tension=tension)


def stroke_fragment(
    system: System,
    fragment: Fragment,
    *,
    thickness: float | None = None,
) -> Drawing:
    """Expand a flourish :class:`Fragment` with the project pen (cubic path)."""
    return stroke(system, fragment, thickness=thickness)

def fuse(drawing: Drawing) -> Drawing:
    """Boolean-simplify overlapping / self-intersecting pen ink into clean contours.

    Multi-stroke constructions (stem + bar, bowl + crossbar) leave intentional
    overlaps; single continuous skeletons can also self-overlap after cubic
    expand (arch joins, tight turns). Mid-master interpolation treats both as
    self-intersection risks. Always pathops-simplify so Light/Bold topology is stable.
    """
    from typekernel.perceive.render import simplify_outline
    from typekernel.plugins.construct import drawing_from_contours

    simplified = simplify_outline(drawing.outline())
    fused = drawing_from_contours(simplified.contours)
    if (drawing.slots or drawing.measures) and len(fused.contours) == len(drawing.contours):
        return Drawing(
            fused.contours,
            fused.roles,
            fused.nodes,
            slots=drawing.slots,
            measures=drawing.measures,
        )
    return fused


def assemble(*parts: Drawing) -> Drawing:
    """Concatenate drawings then :func:`fuse` (preferred multi-stroke return)."""
    if not parts:
        raise ValueError("assemble needs at least one drawing")
    combined = parts[0]
    for part in parts[1:]:
        combined = combined + part
    return fuse(combined)

