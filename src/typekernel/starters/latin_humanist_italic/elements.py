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


def bowl(
    system: System,
    *,
    cx: float,
    cy: float,
    rx: float,
    ry: float,
    thickness: float | None = None,
) -> Drawing:
    """Closed oval ring via the project broad nib (shared by o / zero / eight)."""
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
    n: int = 24,
) -> Drawing:
    """Open elliptical bowl; aperture centered on +x (right) or 180° (left).

    Covers most of the ellipse so stacked s/S / c / three bowls share ink at
    overlaps instead of a private Approximate join.
    """
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
    """Oval bowl nestled against a stem (``side`` is ``"left"`` or ``"right"`` of stem).

    Optional ``cy`` / ``rx`` / ``ry`` override the default x-height bowl metrics
    so capitals (B/P/R) can reuse the same pull.
    """
    st = float(system.stem["lc"]) if thickness is None else float(thickness)
    ov = float(system.overshoot.round)
    rx_v = width * 0.36 if rx is None else float(rx)
    ry_v = (xh / 2.0 + ov * 0.45) if ry is None else float(ry)
    cy_v = (xh / 2.0) if cy is None else float(cy)
    # Pull bowl center toward the stem so overlays share ink instead of a spur gap.
    if side == "right":
        cx = stem_x + rx_v * float(pull)
    elif side == "left":
        cx = stem_x - rx_v * float(pull)
    else:
        raise ValueError(f"side must be left/right, got {side!r}")
    return bowl(system, cx=cx, cy=cy_v, rx=rx_v, ry=ry_v, thickness=st)



def uc_stem(
    system: System,
    x: float,
    *,
    y0: float = 0.0,
    y1: float | None = None,
    thickness: float | None = None,
) -> Drawing:
    """Shared capital vertical stem (H / E / F / K / …)."""
    cap = float(system.zones.cap) if y1 is None else float(y1)
    st = float(system.stem["uc"]) if thickness is None else float(thickness)
    return stroke(system, [(x, y0), (x, cap)], thickness=st)
