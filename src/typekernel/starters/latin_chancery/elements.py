"""Chancery helpers — cubic bowls + internal polyline stroke (S1)."""

from __future__ import annotations

import math
from collections.abc import Sequence

from fontTools.misc.bezierTools import cubicPointAtT

from typekernel.anatomy.pen import (
    bowl as pen_bowl,
)
from typekernel.anatomy.pen import (
    flourish_entry,
    flourish_exit,
    fuse,
    open_arc_points,
    oval_points,
    pen_dot,
    pen_for_optical_stem,
    slanted_centerline,
    slanted_cubic_from_points,
    slanted_vertical_optical_ratio,
)
from typekernel.anatomy.pen import (
    stroke as pen_stroke,
)
from typekernel.anatomy.pen import (
    stroke_fragment as pen_stroke_fragment,
)
from typekernel.draw import Drawing, Fragment
from typekernel.geo.segment import CubicSegment, LineSegment
from typekernel.geo.stroke import Centerline
from typekernel.system import Intent, System
from typekernel.system.intent import pen_for_intent

__all__ = [
    "WIDTHS",
    "bowl",
    "flourish_entry",
    "flourish_exit",
    "fragment_polyline",
    "fuse",
    "n_arch_points",
    "nest_bowl",
    "open_arc_points",
    "open_bowl",
    "oval_points",
    "pen_dot",
    "pen_for_optical_stem",
    "project_pen",
    "slanted_polyline",
    "slanted_vertical_optical_ratio",
    "stroke",
    "stroke_fragment",
    "u_arch_points",
    "uc_stem",
]

WIDTHS: dict[str, float] = {
    "A": 560, "B": 520, "D": 560, "E": 480, "F": 460, "G": 660, "J": 360,
    "K": 520, "L": 460, "M": 700, "N": 560, "P": 500, "R": 540, "S": 480,
    "T": 520, "U": 560, "V": 560, "W": 780, "X": 540, "Y": 540, "Z": 520,
    "e": 400, "emdash": 800, "endash": 400, "g": 420, "hyphen": 200, "k": 420,
    "l": 220, "m": 680, "question": 300, "r": 300, "s": 380, "slash": 280,
    "t": 280, "v": 420, "w": 640, "x": 420, "y": 420, "z": 420,
}


def _project_intent() -> Intent:
    """Read Project.brief.intent — pen choice lives on Intent, not hardcoded nib."""
    try:
        from project import BRIEF

        return BRIEF.intent
    except Exception:  # noqa: BLE001
        return Intent(
            contrast="high",
            slant="italic",
            weight="regular",
            pen_angle_deg=38.0,
            tool="broad",
            connection="partial",
            genre="chancery",
        )


def project_pen(system: System, thickness: float | None = None):
    """Pen from Intent.tool (broad/pointed/monoline/brush), sized to optical stem."""
    optical = float(system.stem["lc"] if thickness is None else thickness)
    # Match prior optical vertical width under slant for broad nibs.
    from typekernel.anatomy.pen import slanted_vertical_optical_ratio

    intent = _project_intent()
    ratio = slanted_vertical_optical_ratio(system) if intent.tool == "broad" else 1.0
    th = float(optical) / ratio if ratio > 0 else float(optical)
    return pen_for_intent(intent, th)


def slanted_polyline(
    points: Sequence[tuple[float, float]],
    system: System,
    *,
    closed: bool = False,
) -> Centerline:
    return slanted_centerline(points, system, closed=closed)


def stroke(
    system: System,
    points: Sequence[tuple[float, float]],
    *,
    closed: bool = False,
    thickness: float | None = None,
) -> Drawing:
    """Stroke via expand using :func:`project_pen` (Intent.tool — not hardcoded nib)."""
    from typekernel.plugins.construct import expand_skeleton

    if closed:
        return pen_stroke(
            system, slanted_cubic_from_points(points, system, closed=True), thickness=thickness
        )
    optical = float(system.stem["lc"] if thickness is None else thickness)
    pen = project_pen(system, optical)
    cl = slanted_centerline(points, system, closed=False)
    return expand_skeleton(cl, pen, join="round", cap="round")


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
    n: int = 36,
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


def stroke_fragment(
    system: System,
    fragment: Fragment,
    *,
    thickness: float | None = None,
) -> Drawing:
    return pen_stroke_fragment(system, fragment, thickness=thickness)


def fragment_polyline(fragment: Fragment, *, samples_per_cubic: int = 8) -> list[tuple[float, float]]:
    pts: list[tuple[float, float]] = []
    for seg in fragment.segments:
        if isinstance(seg, LineSegment):
            for p in (seg.p0, seg.p1):
                pts.append((p.x, p.y))
        elif isinstance(seg, CubicSegment):
            ctrl = [p.as_tuple() for p in seg.points]
            for i in range(samples_per_cubic):
                t = i / (samples_per_cubic - 1)
                x, y = cubicPointAtT(*ctrl, t)
                pts.append((float(x), float(y)))
        else:
            p0 = seg.points[0]
            pts.append((p0.x, p0.y))
    cleaned: list[tuple[float, float]] = []
    for p in pts:
        if not cleaned or math.hypot(p[0] - cleaned[-1][0], p[1] - cleaned[-1][1]) > 0.5:
            cleaned.append(p)
    return cleaned


def n_arch_points(
    x0: float, x1: float, y0: float, y1: float, *, rise: float
) -> list[tuple[float, float]]:
    mid = (x0 + x1) / 2.0
    span = x1 - x0
    return [
        (x0, y0),
        (x0, y1 - rise),
        (x0 + span * 0.18, y1),
        (mid, y1 + rise * 0.2),
        (x1 - span * 0.18, y1),
        (x1, y1 - rise),
        (x1, y0),
    ]


def u_arch_points(
    x0: float, x1: float, y_top: float, *, rise: float
) -> list[tuple[float, float]]:
    mid = (x0 + x1) / 2.0
    span = x1 - x0
    return [
        (x0, y_top),
        (x0, rise),
        (x0 + span * 0.15, 0.0),
        (mid, -rise * 0.15),
        (x1 - span * 0.15, 0.0),
        (x1, rise),
        (x1, y_top),
    ]
