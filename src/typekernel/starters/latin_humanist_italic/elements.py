"""Skeleton helpers for the humanist-italic starter (project-side only)."""

from __future__ import annotations

import math

from typekernel.draw import Drawing
from typekernel.geo.stroke import Centerline
from typekernel.plugins.construct import broad_nib, expand_skeleton
from typekernel.system import System


def _slant_x(x: float, y: float, slant: float) -> float:
    return x + slant * y


def _pen_params(system: System) -> tuple[float, float]:
    """Return ``(pen_contrast, pen_angle_deg)`` from System tokens."""
    contrast = float(system.tokens.get("pen_contrast", 0.55))
    angle = float(system.tokens.get("pen_angle_deg", 30.0))
    return contrast, angle


def slanted_vertical_optical_ratio(system: System) -> float:
    """Horizontal stem width per unit pen thickness for a slanted vertical.

    ``tk audit`` measures filled horizontal spans (``list_vertical_stems``).
    An elliptical broad nib at ``pen_angle_deg`` on a stem leaned by ``System.slant``
    yields optical width ``ratio * thickness``, not ``thickness`` itself.
    Calibrating pens by this ratio keeps System.stem aligned with audit.
    """
    from typekernel.optics.stem import list_vertical_stems

    contrast, angle = _pen_params(system)
    slant = float(system.slant)
    # Unit thickness probe — expand is linear in thickness for this pen model.
    probe_th = 40.0
    cl = slanted_polyline([(200.0, 0.0), (200.0, 500.0)], slant, closed=False)
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


def pen_for_optical_stem(system: System, optical: float):
    """Broad nib whose slanted vertical measures ``optical`` horizontally."""
    contrast, angle = _pen_params(system)
    ratio = slanted_vertical_optical_ratio(system)
    thickness = float(optical) / ratio if ratio > 0 else float(optical)
    return broad_nib(thickness, contrast=contrast, angle_deg=angle)


def project_pen(system: System):
    """Broad nib sized so slanted vertical stems hit ``system.stem['lc']``."""
    return pen_for_optical_stem(system, float(system.stem["lc"]))


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
    """Expand a (pre-slant) polyline with the project broad nib.

    ``thickness`` is the *optical* horizontal stem target (System.stem units),
    not raw ``Pen.thickness`` — elliptical angle + italic slant are calibrated
    out so ``tk audit`` stem checks match the numeric table.
    """
    slant = float(system.slant)
    cl = slanted_polyline(points, slant, closed=closed)
    optical = float(system.stem["lc"]) if thickness is None else float(thickness)
    pen = pen_for_optical_stem(system, optical)
    # Closed rails: bevel required — expand_skeleton rejects join="round" on
    # closed centerlines (VF signature / ink↔counter flip). Open strokes keep
    # round caps/joins for terminal shape.
    join = "bevel" if closed else "round"
    return expand_skeleton(cl, pen, join=join, cap="round")


def diagonal_stroke(
    system: System,
    points: list[tuple[float, float]],
    *,
    thickness: float | None = None,
) -> Drawing:
    """Stroke a diagonal polyline so horizontal stem spans hit ``thickness``.

    Upright ``stroke`` is calibrated for slanted *verticals*. Diagonals read
    wider on a horizontal probe (``tk audit``); scale the optical request so
    the expanded span matches ``System.stem`` without heal/blend passes.
    """
    from typekernel.optics.stem import list_vertical_stems

    if len(points) < 2:
        raise ValueError("diagonal_stroke needs at least two points")
    optical = float(system.stem["lc"]) if thickness is None else float(thickness)
    probe = stroke(system, points, thickness=optical)
    ys = [float(p[1]) for p in points]
    y = 0.5 * (min(ys) + max(ys))
    # Prefer a band away from sharp apex cusps when the path folds.
    if max(ys) - min(ys) > 1.0:
        y = min(ys) + 0.62 * (max(ys) - min(ys))
    try:
        spans = list_vertical_stems(probe.outline(), y=y)
    except Exception:  # noqa: BLE001 - best-effort optical probe
        spans = []
    near = [
        s
        for s in spans
        if s.width > 0 and abs(s.width - optical) / optical <= 0.45
    ]
    if not near:
        return probe
    avg = sum(s.width for s in near) / len(near)
    if avg <= 1e-6:
        return probe
    return stroke(system, points, thickness=optical * (optical / avg))


def oval_points(
    cx: float,
    cy: float,
    rx: float,
    ry: float,
    *,
    n: int = 64,
) -> list[tuple[float, float]]:
    """Unslanted oval sample points (closed centerline).

    Default ``n=64`` is dense enough for broad-nib expand; keep it **fixed**
    across masters (do not derive from rx/ry) so VF signatures stay stable.
    For a budget-based count at design time, see ``ellipse_point_count``.
    """
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
    """Unslanted elliptical arc samples (open centerline), degrees CCW from +x.

    Fixed default ``n`` (not rx-derived) keeps Light/Bold topology aligned.
    """
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
    n: int = 48,
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
