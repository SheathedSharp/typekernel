"""Skeleton helpers for the humanist-italic starter (project-side only)."""

from __future__ import annotations

import math

from typekernel.draw import Drawing
from typekernel.geo.stroke import Centerline
from typekernel.plugins.construct import broad_nib, expand_skeleton
from typekernel.system import System


def _slant_x(x: float, y: float, slant: float) -> float:
    return x + slant * y


def project_pen(system: System):
    """Broad nib sized from ``system.stem['lc']`` and pen tokens."""
    thickness = float(system.stem["lc"])
    contrast = float(system.tokens.get("pen_contrast", 0.55))
    angle = float(system.tokens.get("pen_angle_deg", 30.0))
    return broad_nib(thickness, contrast=contrast, angle_deg=angle)


def slanted_polyline(
    points: list[tuple[float, float]],
    slant: float,
    *,
    closed: bool = False,
) -> Centerline:
    slanted = [(_slant_x(x, y, slant), y) for x, y in points]
    return Centerline.from_points(slanted, closed=closed)


def stroke(
    system: System,
    points: list[tuple[float, float]],
    *,
    closed: bool = False,
    thickness: float | None = None,
) -> Drawing:
    """Expand a (pre-slant) polyline with the project broad nib."""
    slant = float(system.tokens.get("slant", 0.0))
    cl = slanted_polyline(points, slant, closed=closed)
    if thickness is None:
        pen = project_pen(system)
    else:
        pen = broad_nib(
            float(thickness),
            contrast=float(system.tokens.get("pen_contrast", 0.55)),
            angle_deg=float(system.tokens.get("pen_angle_deg", 30.0)),
        )
    # Closed rails: bevel keeps offset point order thickness-stable for VF
    # (elliptical round joins reverse the counter under Bold). Open strokes keep
    # round caps/joins for terminal shape.
    join = "bevel" if closed else "round"
    return expand_skeleton(cl, pen, join=join, cap="round")


def oval_points(
    cx: float,
    cy: float,
    rx: float,
    ry: float,
    *,
    n: int = 28,
) -> list[tuple[float, float]]:
    """Unslanted oval sample points (closed centerline)."""
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
    n: int = 20,
) -> list[tuple[float, float]]:
    """Unslanted elliptical arc samples (open centerline), degrees CCW from +x."""
    a0 = math.radians(start_deg)
    a1 = math.radians(end_deg)
    # Go the short/long way as given (end may be < start for clockwise).
    return [
        (
            cx + rx * math.cos(a0 + (a1 - a0) * i / (n - 1)),
            cy + ry * math.sin(a0 + (a1 - a0) * i / (n - 1)),
        )
        for i in range(n)
    ]


def nest_bowl(
    system: System,
    *,
    stem_x: float,
    side: str,
    width: float,
    xh: float,
    lsb: float,
    thickness: float | None = None,
) -> Drawing:
    """Oval bowl nestled against a stem (``side`` is ``"left"`` or ``"right"`` of stem)."""
    st = float(system.stem["lc"]) if thickness is None else float(thickness)
    ov = float(system.overshoot.round)
    rx = width * 0.36
    ry = xh / 2.0 + ov * 0.45
    cy = xh / 2.0
    # Pull bowl center toward the stem so overlays share ink instead of a spur gap.
    if side == "right":
        cx = stem_x + rx * 0.78
    elif side == "left":
        cx = stem_x - rx * 0.78
    else:
        raise ValueError(f"side must be left/right, got {side!r}")
    return stroke(
        system,
        oval_points(cx, cy, rx, ry),
        closed=True,
        thickness=st,
    )

