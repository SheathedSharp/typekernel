"""Humanist-italic helpers — anatomy.pen shim (S1 cubic bowls + tidy).

Open ``stroke`` uses polyline expand as an *internal* implementation detail,
then compile-time tidy. Closed bowls use κ-ellipse cubics + curve-aware expand.
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
    slanted_cubic_from_points,
    slanted_vertical_optical_ratio,
)
from typekernel.anatomy.pen import (
    bowl as pen_bowl,
)
from typekernel.anatomy.pen import (
    open_bowl as pen_open_bowl,
)
from typekernel.anatomy.pen import (
    stroke as pen_stroke,
)
from typekernel.draw import Drawing
from typekernel.geo.stroke import Centerline
from typekernel.system import System

__all__ = [
    "WIDTHS",
    "assemble",
    "bowl",
    "diagonal_stroke",
    "fuse",
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

WIDTHS: dict[str, float] = {
    "A": 620, "B": 560, "D": 600, "E": 500, "F": 460, "G": 640, "J": 460,
    "K": 580, "L": 480, "M": 760, "N": 600, "P": 520, "R": 580, "S": 540,
    "T": 560, "U": 600, "V": 620, "W": 900, "X": 600, "Y": 600, "Z": 560,
    "emdash": 800, "endash": 400, "f": 260, "fig": 460, "g": 420, "hyphen": 200,
    "k": 400, "m": 640, "question": 300, "r": 280, "s": 360, "slash": 280,
    "t": 280, "v": 400, "w": 620, "x": 400, "y": 400, "z": 400,
}


def slanted_polyline(
    points: Sequence[tuple[float, float]],
    slant: float,
    *,
    closed: bool = False,
) -> Centerline:
    slanted = [(float(x) + float(slant) * float(y), float(y)) for x, y in points]
    return Centerline.from_points(slanted, closed=closed)


def stroke(
    system: System,
    points: Sequence[tuple[float, float]],
    *,
    closed: bool = False,
    thickness: float | None = None,
) -> Drawing:
    """Open: internal polyline expand + tidy. Closed: cubic fit + curve expand."""
    if closed:
        return pen_stroke(
            system, slanted_cubic_from_points(points, system, closed=True), thickness=thickness
        )
    return expand_slanted_centerline(
        system, slanted_centerline(points, system, closed=False), thickness=thickness
    )


def bowl(
    system: System,
    *,
    cx: float,
    cy: float,
    rx: float,
    ry: float,
    thickness: float | None = None,
) -> Drawing:
    return pen_bowl(system, cx=cx, cy=cy, rx=rx, ry=ry, thickness=thickness)


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
    return pen_open_bowl(
        system,
        cx=cx,
        cy=cy,
        rx=rx,
        ry=ry,
        thickness=thickness,
        open_side=open_side,
        aperture_deg=aperture_deg,
        n=n,
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
    del lsb
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
    except (ValueError, TypeError, KeyError):
        spans = []
    near = [s for s in spans if s.width > 0 and abs(s.width - optical) / optical <= 0.45]
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
