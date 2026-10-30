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

__all__ = [
    "WIDTHS","fuse", "open_arc_points", "open_bowl", "oval_points", "stroke", "uc_stem"]

# Per-glyph widths (not System control tokens). Control words n/o/H/O stay on System.tokens.
WIDTHS: dict[str, float] = {
    "A": 640,
    "B": 580,
    "D": 620,
    "E": 520,
    "F": 480,
    "G": 660,
    "I": 220,
    "J": 480,
    "K": 600,
    "L": 500,
    "M": 780,
    "N": 620,
    "P": 540,
    "R": 600,
    "S": 560,
    "T": 560,
    "U": 620,
    "V": 640,
    "W": 920,
    "X": 620,
    "Y": 620,
    "Z": 580,
    "emdash": 800,
    "endash": 400,
    "f": 260,
    "fig": 460,
    "g": 420,
    "hyphen": 200,
    "k": 420,
    "l": 220,
    "m": 680,
    "question": 300,
    "r": 300,
    "s": 380,
    "slash": 280,
    "t": 280,
    "v": 420,
    "w": 640,
    "x": 420,
    "y": 420,
    "z": 420,
}


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
