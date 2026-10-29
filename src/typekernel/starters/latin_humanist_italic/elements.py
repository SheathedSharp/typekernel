"""Humanist-italic project helpers — thin shim over :mod:`typekernel.anatomy.pen`.

Glyph polyline ``stroke`` / bowls keep the hash-stable expand path. Kernel
:func:`~typekernel.anatomy.pen.stroke` accepts cubics only (P5-1).
"""

from __future__ import annotations

from collections.abc import Sequence

from typekernel.anatomy.pen import (
    assemble,
    expand_slanted_centerline,
    fuse,
    open_arc_points,
    oval_points,
    pen_for_optical_stem,
    project_pen,
    slanted_centerline,
    slanted_vertical_optical_ratio,
)
from typekernel.draw import Drawing
from typekernel.geo.stroke import Centerline
from typekernel.system import System

__all__ = [
    "assemble",
    "bowl",
    "fuse",
    "diagonal_stroke",
    "nest_bowl",
    "open_arc_points",
    "open_bowl",
    "oval_points",
    "pen_for_optical_stem",
    "project_pen",
    "slanted_polyline",
    "slanted_vertical_optical_ratio",
    "stroke",
    "uc_stem",
]


def slanted_polyline(
    points: Sequence[tuple[float, float]],
    slant: float,
    *,
    closed: bool = False,
) -> Centerline:
    """Legacy signature ``(points, slant)`` — prefer :func:`slanted_centerline`."""
    slanted = [(float(x) + float(slant) * float(y), float(y)) for x, y in points]
    return Centerline.from_points(slanted, closed=closed)


def stroke(
    system: System,
    points: Sequence[tuple[float, float]],
    *,
    closed: bool = False,
    thickness: float | None = None,
) -> Drawing:
    """Expand upright polyline points (hash-stable polyline expand)."""
    cl = slanted_centerline(points, system, closed=closed)
    return expand_slanted_centerline(system, cl, thickness=thickness)


def bowl(
    system: System,
    *,
    cx: float,
    cy: float,
    rx: float,
    ry: float,
    thickness: float | None = None,
) -> Drawing:
    st = float(system.stem["lc"]) if thickness is None else float(thickness)
    return stroke(system, oval_points(cx, cy, rx, ry), closed=True, thickness=st)


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
    if open_side not in ("right", "left"):
        raise ValueError(f"open_side must be 'right' or 'left', got {open_side!r}")
    st = float(system.stem["lc"]) if thickness is None else float(thickness)
    half = float(aperture_deg) / 2.0
    if open_side == "right":
        start_deg, end_deg = half, 360.0 - half
    else:
        start_deg, end_deg = 180.0 + half, 180.0 - half + 360.0
    return stroke(
        system,
        open_arc_points(cx, cy, rx, ry, start_deg=start_deg, end_deg=end_deg, n=n),
        thickness=st,
    )


def nest_bowl(
    system: System,
    *,
    stem_x: float,
    side: str,
    width: float,
    xh: float,
    lsb: float,
    thickness: float | None = None,
    cy: float | None = None,
    rx: float | None = None,
    ry: float | None = None,
    pull: float = 0.78,
) -> Drawing:
    st = float(system.stem["lc"]) if thickness is None else float(thickness)
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
    return bowl(system, cx=cx, cy=cy_v, rx=rx_v, ry=ry_v, thickness=st)


def diagonal_stroke(
    system: System,
    points: list[tuple[float, float]],
    *,
    thickness: float | None = None,
) -> Drawing:
    from typekernel.optics.stem import list_vertical_stems

    if len(points) < 2:
        raise ValueError("diagonal_stroke needs at least two points")
    optical = float(system.stem["lc"]) if thickness is None else float(thickness)
    probe = stroke(system, points, thickness=optical)
    ys = [float(p[1]) for p in points]
    y = 0.5 * (min(ys) + max(ys))
    if max(ys) - min(ys) > 1.0:
        y = min(ys) + 0.62 * (max(ys) - min(ys))
    try:
        spans = list_vertical_stems(probe.outline(), y=y)
    except Exception:  # noqa: BLE001
        spans = []
    near = [
        s for s in spans if s.width > 0 and abs(s.width - optical) / optical <= 0.45
    ]
    if not near:
        return probe
    avg = sum(s.width for s in near) / len(near)
    if avg <= 1e-6:
        return probe
    return stroke(system, points, thickness=optical * (optical / avg))


def uc_stem(
    system: System,
    x: float,
    *,
    y0: float = 0.0,
    y1: float | None = None,
    thickness: float | None = None,
) -> Drawing:
    cap = float(system.zones.cap) if y1 is None else float(y1)
    st = float(system.stem["uc"]) if thickness is None else float(thickness)
    return stroke(system, [(x, y0), (x, cap)], thickness=st)
