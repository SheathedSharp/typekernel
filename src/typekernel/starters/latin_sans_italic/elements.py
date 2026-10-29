"""latin-sans italic helpers — polyline shim over anatomy.pen."""

from __future__ import annotations

from collections.abc import Sequence

from typekernel.anatomy.pen import (
    expand_slanted_centerline,
    fuse,
    open_arc_points,
    oval_points,
    slanted_centerline,
)
from typekernel.anatomy.pen import (
    open_bowl as pen_open_bowl,
)
from typekernel.draw import Drawing
from typekernel.system import System

__all__ = ["fuse", "open_arc_points", "open_bowl", "oval_points", "stroke", "uc_stem"]


def stroke(
    system: System,
    points: Sequence[tuple[float, float]],
    *,
    closed: bool = False,
    thickness: float | None = None,
) -> Drawing:
    cl = slanted_centerline(points, system, closed=closed)
    return expand_slanted_centerline(system, cl, thickness=thickness)


def open_bowl(
    system: System,
    *,
    cx: float,
    cy: float,
    rx: float,
    ry: float,
    thickness: float | None = None,
    open_side: str = "right",
    aperture_deg: float | None = None,
) -> Drawing:
    """Open bowl via kernel cubic path (new drawings — hash not constrained)."""
    deg = float(
        system.tokens.get("bowl_aperture_deg", 72.0) if aperture_deg is None else aperture_deg
    )
    return pen_open_bowl(
        system,
        cx=cx,
        cy=cy,
        rx=rx,
        ry=ry,
        thickness=thickness,
        open_side=open_side,
        aperture_deg=deg,
    )


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
