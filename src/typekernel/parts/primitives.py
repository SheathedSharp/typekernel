"""Reusable glyph parts — the Mesh / geometry primitives of type design.

Each factory returns a cubic :class:`~typekernel.geo.outline.Outline` sized from
a shared :class:`~typekernel.parts.context.DesignContext`, so composing letters
is closer to assembling Three.js meshes than redrawing Béziers per glyph.
"""

from __future__ import annotations

import math

from typekernel.geo.outline import Outline
from typekernel.geo.path_builder import PathBuilder
from typekernel.geo.path_helpers import KAPPA
from typekernel.parts.context import DesignContext
from typekernel.parts.transforms import rotate


def vertical_stem(
    ctx: DesignContext,
    x_left: float,
    y_bottom: float,
    y_top: float,
    *,
    width: float | None = None,
) -> Outline:
    """Axis-aligned vertical stem rectangle."""
    w = ctx.stem if width is None else width
    return _rect(x_left, y_bottom, x_left + w, y_top)


def horizontal_bar(
    ctx: DesignContext,
    x_left: float,
    x_right: float,
    y_bottom: float,
    *,
    thickness: float | None = None,
) -> Outline:
    """Axis-aligned horizontal bar."""
    t = ctx.thin if thickness is None else thickness
    return _rect(x_left, y_bottom, x_right, y_bottom + t)


def rounded_rect(
    ctx: DesignContext,
    x0: float,
    y0: float,
    x1: float,
    y1: float,
    *,
    radius: float | None = None,
) -> Outline:
    """Rectangle with optional corner fillets from ``ctx.roundness``."""
    r = ctx.join_radius if radius is None else radius
    if r <= 0:
        return _rect(x0, y0, x1, y1)
    r = min(r, abs(x1 - x0) / 2.0, abs(y1 - y0) / 2.0)
    b = PathBuilder()
    b.moveTo(x0 + r, y0)
    b.lineTo(x1 - r, y0)
    b.curveTo(x1 - r + r * KAPPA, y0, x1, y0 + r - r * KAPPA, x1, y0 + r)
    b.lineTo(x1, y1 - r)
    b.curveTo(x1, y1 - r + r * KAPPA, x1 - r + r * KAPPA, y1, x1 - r, y1)
    b.lineTo(x0 + r, y1)
    b.curveTo(x0 + r - r * KAPPA, y1, x0, y1 - r + r * KAPPA, x0, y1 - r)
    b.lineTo(x0, y0 + r)
    b.curveTo(x0, y0 + r - r * KAPPA, x0 + r - r * KAPPA, y0, x0 + r, y0)
    b.closePath()
    return b.build()


def bowl(
    ctx: DesignContext,
    cx: float,
    cy: float,
    *,
    rx: float | None = None,
    ry: float | None = None,
    thickness: float | None = None,
    thickness_v: float | None = None,
    thickness_h: float | None = None,
    shape: str = "ellipse",
    n: float = 2.0,
    tension: float = 1.0,
) -> tuple[Outline, Outline]:
    """Bowl ring: returns ``(outer, counter)``.

    ``shape`` is ``"ellipse"`` (default, κ-handles) or ``"superellipse"``
    (Lamé exponent ``n``, handle tension). Outer radius defaults to half
    x-height plus overshoot on the vertical axis. Counter inset uses
    vertical stroke ``thickness_v`` (default ``ctx.stem``) and horizontal
    ``thickness_h`` (default ``ctx.thin``). A single ``thickness`` sets both.
    """
    outer_ry = (ctx.x_height / 2.0 + ctx.overshoot) if ry is None else ry
    outer_rx = outer_ry if rx is None else rx
    if thickness is not None:
        tv = th = thickness
    else:
        tv = ctx.stem if thickness_v is None else thickness_v
        th = ctx.thin if thickness_h is None else thickness_h
    inner_rx = max(outer_rx - tv, 1.0)
    inner_ry = max(outer_ry - th, 1.0)
    if shape == "ellipse":
        if abs(n - 2.0) > 1e-12 or abs(tension - 1.0) > 1e-12:
            # Explicit n/tension on ellipse shape → treat as superellipse
            shape = "superellipse"
        else:
            return (
                _ellipse(cx, cy, outer_rx, outer_ry),
                _stress_inner(ctx, cx, cy, _ellipse(cx, cy, inner_rx, inner_ry)),
            )
    if shape == "superellipse":
        from typekernel.geo.curves import superellipse_outline

        return (
            superellipse_outline(cx, cy, outer_rx, outer_ry, n, tension=tension),
            _stress_inner(
                ctx,
                cx,
                cy,
                superellipse_outline(cx, cy, inner_rx, inner_ry, n, tension=tension),
            ),
        )
    raise ValueError(f"unknown bowl shape: {shape!r} (use 'ellipse' or 'superellipse')")


def _stress_inner(ctx: DesignContext, cx: float, cy: float, hole: Outline) -> Outline:
    if abs(ctx.stress) < 1e-9:
        return hole
    return rotate(hole, ctx.stress, origin=(cx, cy))


def superellipse_ring(
    ctx: DesignContext,
    cx: float,
    cy: float,
    *,
    rx: float | None = None,
    ry: float | None = None,
    thickness: float | None = None,
    n: float = 2.5,
    tension: float = 1.0,
) -> tuple[Outline, Outline]:
    """Convenience: :func:`bowl` with ``shape="superellipse"``."""
    return bowl(
        ctx,
        cx,
        cy,
        rx=rx,
        ry=ry,
        thickness=thickness,
        shape="superellipse",
        n=n,
        tension=tension,
    )


def counter(
    ctx: DesignContext,
    cx: float,
    cy: float,
    rx: float,
    ry: float,
) -> Outline:
    """Standalone elliptical hole (clockwise or CCW — winding fixed at union)."""
    del ctx
    return _ellipse(cx, cy, rx, ry)


def arch(
    ctx: DesignContext,
    x_left: float,
    x_right: float,
    y_bottom: float,
    y_top: float,
    *,
    thickness: float | None = None,
    meet_fillet: float | None = None,
) -> Outline:
    """n/h-style shoulder: outer and inner arches forming a closed trough top.

    The arch sits between two imaginary stems at ``x_left`` and ``x_right``
    (inner faces). ``y_top`` is the outer crown; ``y_bottom`` is where the arch
    meets the stem tops internally.

    ``meet_fillet`` (default ``ctx.join_radius * 0.35``) rounds the four
    stem-meet corners on the path itself so a later boolean with stems is less
    likely to leave a hard T-junction. Pass ``0`` for the old square meets.
    For a full n/h body with **no** boolean seam, prefer :func:`shoulder_yoke`.
    """
    t = ctx.stem if thickness is None else thickness
    mid = (x_left + x_right) / 2.0
    span = x_right - x_left
    fillet = ctx.join_radius * 0.35 if meet_fillet is None else meet_fillet
    fillet = max(0.0, min(fillet, t * 0.45, span * 0.12))
    # Outer path: left top -> crown -> right top -> down inner -> inner crown -> back
    b = PathBuilder()
    if fillet <= 0:
        b.moveTo(x_left, y_bottom)
    else:
        # Fillet SW outer meet: start on bottom, curve onto left outer rise.
        b.moveTo(x_left + fillet, y_bottom)
        b.curveTo(
            x_left + fillet * 0.45,
            y_bottom,
            x_left,
            y_bottom + fillet * 0.45,
            x_left,
            y_bottom + fillet,
        )
    b.lineTo(x_left, y_top - span * 0.15)
    # Outer crown (smooth)
    b.smoothCurveTo(
        mid,
        y_top,
        tangent_out_x=1.0,
        tangent_out_y=0.0,
        handle_ratio=0.42,
        tangent_in_x=0.0,
        tangent_in_y=1.0,
    )
    b.smoothCurveTo(
        x_right,
        y_top - span * 0.15,
        tangent_out_x=0.0,
        tangent_out_y=-1.0,
        handle_ratio=0.42,
        tangent_in_x=1.0,
        tangent_in_y=0.0,
    )
    if fillet <= 0:
        b.lineTo(x_right, y_bottom)
        b.lineTo(x_right - t, y_bottom)
    else:
        b.lineTo(x_right, y_bottom + fillet)
        b.curveTo(
            x_right,
            y_bottom + fillet * 0.45,
            x_right - fillet * 0.45,
            y_bottom,
            x_right - fillet,
            y_bottom,
        )
        b.lineTo(x_right - t + fillet, y_bottom)
        b.curveTo(
            x_right - t + fillet * 0.45,
            y_bottom,
            x_right - t,
            y_bottom + fillet * 0.45,
            x_right - t,
            y_bottom + fillet,
        )
    inner_top = y_top - t
    b.lineTo(x_right - t, inner_top - span * 0.12)
    b.smoothCurveTo(
        mid,
        inner_top,
        tangent_out_x=-1.0,
        tangent_out_y=0.0,
        handle_ratio=0.42,
        tangent_in_x=0.0,
        tangent_in_y=1.0,
    )
    b.smoothCurveTo(
        x_left + t,
        inner_top - span * 0.12,
        tangent_out_x=0.0,
        tangent_out_y=-1.0,
        handle_ratio=0.42,
        tangent_in_x=-1.0,
        tangent_in_y=0.0,
    )
    if fillet <= 0:
        b.lineTo(x_left + t, y_bottom)
    else:
        b.lineTo(x_left + t, y_bottom + fillet)
        b.curveTo(
            x_left + t,
            y_bottom + fillet * 0.45,
            x_left + t - fillet * 0.45,
            y_bottom,
            x_left + t - fillet,
            y_bottom,
        )
        b.lineTo(x_left + fillet, y_bottom)
    b.closePath()
    return b.build()


def u_bowl(
    ctx: DesignContext,
    x_left: float,
    x_right: float,
    y_top: float,
    y_bottom: float,
    *,
    thickness: float | None = None,
) -> Outline:
    """U-shaped trough (two stems + rounded bottom) as one closed outline."""
    t = ctx.stem if thickness is None else thickness
    mid = (x_left + x_right) / 2.0
    depth = (x_right - x_left) * 0.48
    b = PathBuilder()
    # Outer: down left, bottom arc, up right
    b.moveTo(x_left, y_top)
    b.lineTo(x_left, y_bottom + depth)
    b.smoothCurveTo(
        mid,
        y_bottom,
        tangent_out_x=1.0,
        tangent_out_y=0.0,
        handle_ratio=0.45,
        tangent_in_x=0.0,
        tangent_in_y=-1.0,
    )
    b.smoothCurveTo(
        x_right,
        y_bottom + depth,
        tangent_out_x=0.0,
        tangent_out_y=1.0,
        handle_ratio=0.45,
        tangent_in_x=1.0,
        tangent_in_y=0.0,
    )
    b.lineTo(x_right, y_top)
    b.lineTo(x_right - t, y_top)
    b.lineTo(x_right - t, y_bottom + depth)
    inner_bottom = y_bottom + t
    b.smoothCurveTo(
        mid,
        inner_bottom,
        tangent_out_x=-1.0,
        tangent_out_y=0.0,
        handle_ratio=0.45,
        tangent_in_x=0.0,
        tangent_in_y=-1.0,
    )
    b.smoothCurveTo(
        x_left + t,
        y_bottom + depth,
        tangent_out_x=0.0,
        tangent_out_y=1.0,
        handle_ratio=0.45,
        tangent_in_x=-1.0,
        tangent_in_y=0.0,
    )
    b.lineTo(x_left + t, y_top)
    b.closePath()
    return b.build()


def diagonal_stem(
    ctx: DesignContext,
    x0: float,
    y0: float,
    x1: float,
    y1: float,
    *,
    width: float | None = None,
    compensate: bool = False,
) -> Outline:
    """Thickened line segment (parallelogram) for diagonals in ``z`` / ``y``.

    When ``compensate`` is True and ``width`` is omitted, the perpendicular
    thickness is taken from
    :func:`~typekernel.optics.stem.diagonal_compensation` so the bar matches
    the apparent weight of ``ctx.stem`` (vertical). Explicit ``width`` always
    wins and is never auto-thinned.
    """
    dx, dy = x1 - x0, y1 - y0
    length = math.hypot(dx, dy) or 1.0
    if width is not None:
        w = width
    elif compensate:
        from typekernel.optics.stem import diagonal_compensation

        # Angle from vertical: vertical = (0,1) → atan2(dx, dy)
        angle_from_vertical = math.degrees(math.atan2(abs(dx), abs(dy)))
        w = diagonal_compensation(angle_from_vertical, ctx.stem, contrast=ctx.contrast)
    else:
        w = ctx.stem
    nx, ny = -dy / length, dx / length
    half = w / 2.0
    b = PathBuilder()
    b.moveTo(x0 + nx * half, y0 + ny * half)
    b.lineTo(x1 + nx * half, y1 + ny * half)
    b.lineTo(x1 - nx * half, y1 - ny * half)
    b.lineTo(x0 - nx * half, y0 - ny * half)
    b.closePath()
    return b.build()


def hook_terminal(
    ctx: DesignContext,
    x_center: float,
    y_top: float,
    y_bottom: float,
    *,
    hook_radius: float | None = None,
    width: float | None = None,
) -> Outline:
    """Descending stem with a leftward curved hook (lowercase ``j``).

    Outer arc centre sits so the stem's right edge is the arc's east point;
    the hook sweeps through south to the west (open to the left).
    """
    t = ctx.stem if width is None else width
    hr = (abs(y_bottom) * 0.50) if hook_radius is None else hook_radius
    hr = max(hr, t * 1.2)
    left = x_center - t / 2.0
    right = x_center + t / 2.0
    # East point of outer arc == (right, y_bottom + hr)
    outer_cx = right - hr
    outer_cy = y_bottom + hr
    ir = hr - t
    inner_cx = outer_cx
    inner_cy = outer_cy

    b = PathBuilder()
    b.moveTo(left, y_top)
    b.lineTo(right, y_top)
    b.lineTo(right, y_bottom + hr)
    # Outer: 0° (east) → -180° (west), CCW negative = clockwise sweep southward
    b.arcTo(outer_cx, outer_cy, hr, hr, -180, start_angle_deg=0)
    # Now at west outer: (outer_cx - hr, outer_cy)
    # Cap the hook terminal with the stem thickness
    b.lineTo(outer_cx - ir, outer_cy)
    # Inner arc back: 180° → 0° (west to east on inner circle)
    b.arcTo(inner_cx, inner_cy, ir, ir, 0, start_angle_deg=180)
    # Now at (outer_cx + ir, outer_cy) which should be near (left, y_bottom+hr)
    b.lineTo(left, y_bottom + hr)
    b.closePath()
    return b.build()



def tittle(
    ctx: DesignContext,
    cx: float,
    y_bottom: float,
    *,
    size: float | None = None,
) -> Outline:
    """Dot above ``i`` / ``j``; shape from ``ctx.style.i_dot``."""
    s = ctx.stem * 0.95 if size is None else size
    w = s * ctx.contrast
    x0, x1 = cx - w / 2.0, cx + w / 2.0
    y0, y1 = y_bottom, y_bottom + s
    kind = ctx.style.i_dot
    if kind == "square":
        return rounded_rect(ctx, x0, y0, x1, y1, radius=0.0)
    if kind == "diamond":
        from typekernel.geo.contour import reverse_contour

        mid_y = (y0 + y1) / 2.0
        b = PathBuilder()
        b.moveTo(cx, y1)
        b.lineTo(x1, mid_y)
        b.lineTo(cx, y0)
        b.lineTo(x0, mid_y)
        b.closePath()
        (contour,) = b.build().contours
        return Outline((reverse_contour(contour),))
    r = min(ctx.join_radius * 0.6, min(w, s) * 0.35)
    return rounded_rect(ctx, x0, y0, x1, y1, radius=r)


def contrast_stem_caps(
    ctx: DesignContext,
    x_left: float,
    y_bottom: float,
    y_top: float,
    *,
    width: float | None = None,
) -> Outline:
    """Vertical stem that tapers horizontally when ``contrast`` ≠ 1."""
    w = ctx.stem if width is None else width
    if abs(ctx.contrast - 1.0) < 1e-9:
        return _rect(x_left, y_bottom, x_left + w, y_top)
    inset = (w - w * ctx.contrast) / 2.0
    pts = [
        (x_left, y_bottom),
        (x_left + w, y_bottom),
        (x_left + w - inset, y_top),
        (x_left + inset, y_top),
    ]
    b = PathBuilder()
    b.moveTo(*pts[0])
    for p in pts[1:]:
        b.lineTo(*p)
    b.closePath()
    return b.build()


def _rect(x0: float, y0: float, x1: float, y1: float) -> Outline:
    b = PathBuilder()
    b.moveTo(x0, y0)
    b.lineTo(x1, y0)
    b.lineTo(x1, y1)
    b.lineTo(x0, y1)
    b.closePath()
    return b.build()


def _ellipse(cx: float, cy: float, rx: float, ry: float) -> Outline:
    b = PathBuilder()
    b.addEllipse(cx, cy, rx, ry)
    return b.build()


def stroke_polyline(
    ctx: DesignContext,
    points: list[tuple[float, float]],
    *,
    width: float | None = None,
    join_radius: float | None = None,
) -> Outline:
    """Centered stroke of a polyline; optional rounded joins from ``ctx.roundness``."""
    import math

    thickness = ctx.stem if width is None else width
    radius = ctx.join_radius if join_radius is None else join_radius
    half = thickness / 2.0
    n = len(points)
    if n < 2:
        raise ValueError("stroke_polyline needs at least two points")

    def seg_n(i: int) -> tuple[float, float]:
        dx = points[i + 1][0] - points[i][0]
        dy = points[i + 1][1] - points[i][1]
        ln = math.hypot(dx, dy) or 1.0
        return (-dy / ln, dx / ln)

    normals = [seg_n(i) for i in range(n - 1)]
    left: list[tuple[float, float]] = []
    right: list[tuple[float, float]] = []
    for i in range(n):
        if i == 0:
            nx, ny = normals[0]
        elif i == n - 1:
            nx, ny = normals[-1]
        else:
            ax, ay = normals[i - 1]
            bx, by = normals[i]
            sx, sy = ax + bx, ay + by
            sl = math.hypot(sx, sy)
            if sl < 1e-6:
                nx, ny = ax, ay
            else:
                nx, ny = sx / sl, sy / sl
                dot = max(-1.0, min(1.0, ax * nx + ay * ny))
                m = min(1.0 / max(dot, 0.45), 2.2)
                nx, ny = nx * m, ny * m
        left.append((points[i][0] + nx * half, points[i][1] + ny * half))
        right.append((points[i][0] - nx * half, points[i][1] - ny * half))

    b = PathBuilder()
    if radius <= 0 or n < 3:
        b.moveTo(*left[0])
        for pt in left[1:]:
            b.lineTo(*pt)
        b.lineTo(*right[-1])
        for pt in reversed(right[:-1]):
            b.lineTo(*pt)
        b.closePath()
        return b.build()

    b.moveTo(*left[0])
    for i in range(1, len(left) - 1):
        b.roundedCornerTo(
            left[i][0], left[i][1], left[i + 1][0], left[i + 1][1], radius, continue_to_end=False
        )
    b.lineTo(*left[-1])
    b.lineTo(*right[-1])
    for i in range(len(right) - 2, 0, -1):
        nxt = right[i - 1]
        b.roundedCornerTo(
            right[i][0], right[i][1], nxt[0], nxt[1], radius, continue_to_end=False
        )
    b.lineTo(*right[0])
    b.closePath()
    return b.build()



# ---------------------------------------------------------------------------
# Extra primitives for agent composition (Three.js-style catalog depth)
# ---------------------------------------------------------------------------


def capsule(
    ctx: DesignContext,
    x0: float,
    y0: float,
    x1: float,
    y1: float,
    *,
    radius: float | None = None,
) -> Outline:
    """Stadium / capsule: rectangle with semicircle caps on the short axis.

    Useful for soft terminals and even-colour bars without sharp corners.
    """
    r = (min(abs(x1 - x0), abs(y1 - y0)) / 2.0) if radius is None else radius
    # Orient: if wider than tall, caps on left/right; else top/bottom.
    w, h = abs(x1 - x0), abs(y1 - y0)
    b = PathBuilder()
    if w >= h:
        r = min(r, h / 2.0)
        cy = (y0 + y1) / 2.0
        left_cx, right_cx = x0 + r, x1 - r
        b.moveTo(left_cx, y0)
        b.lineTo(right_cx, y0)
        b.arcTo(right_cx, cy, r, r, 270, start_angle_deg=-90)
        b.lineTo(left_cx, y1)
        b.arcTo(left_cx, cy, r, r, 90, start_angle_deg=90)
        b.closePath()
    else:
        r = min(r, w / 2.0)
        cx = (x0 + x1) / 2.0
        bot_cy, top_cy = y0 + r, y1 - r
        b.moveTo(x0, bot_cy)
        b.arcTo(cx, bot_cy, r, r, 0, start_angle_deg=180)
        b.lineTo(x1, top_cy)
        b.arcTo(cx, top_cy, r, r, 180, start_angle_deg=0)
        b.closePath()
    return b.build()


def crossbar(
    ctx: DesignContext,
    x_left: float,
    x_right: float,
    y_center: float,
    *,
    thickness: float | None = None,
) -> Outline:
    """Centered horizontal crossbar (``e``, ``A``, ``H``)."""
    t = ctx.thin if thickness is None else thickness
    return horizontal_bar(ctx, x_left, x_right, y_center - t / 2.0, thickness=t)


def wedge(
    ctx: DesignContext,
    tip_x: float,
    tip_y: float,
    base_x0: float,
    base_y0: float,
    base_x1: float,
    base_y1: float,
) -> Outline:
    """Triangle wedge — building block for ink traps and tapered joins."""
    del ctx
    b = PathBuilder()
    b.moveTo(tip_x, tip_y)
    b.lineTo(base_x0, base_y0)
    b.lineTo(base_x1, base_y1)
    b.closePath()
    return b.build()


def fillet_pad(
    ctx: DesignContext,
    x: float,
    y: float,
    *,
    radius: float | None = None,
    quadrant: int = 0,
) -> Outline:
    """Quarter-disk pad to soften a stem/bowl join before boolean union.

    ``quadrant`` 0..3 matches quarter-circle cubics (0=NE, 1=NW, 2=SW, 3=SE).
    Place the pad so its centre sits at the concave notch corner, then call
    :meth:`~typekernel.parts.compose.GlyphAssembler.union_solids`.
    """
    from typekernel.geo.path_helpers import Quadrant, quarter_circle_cubics

    r = ctx.join_radius if radius is None else radius
    if r <= 0:
        return _rect(x, y, x + 1e-3, y + 1e-3)
    q = quadrant % 4
    p0, p1, p2, p3 = quarter_circle_cubics(x, y, r, r, q)  # type: ignore[arg-type]
    del Quadrant  # imported for agents reading the signature docs
    b = PathBuilder()
    b.moveTo(x, y)
    b.lineTo(p0.x, p0.y)
    b.curveTo(p1.x, p1.y, p2.x, p2.y, p3.x, p3.y)
    b.closePath()
    return b.build()


def terminal_ball(
    ctx: DesignContext,
    cx: float,
    cy: float,
    *,
    radius: float | None = None,
) -> Outline:
    """Circular ball terminal (stroke end blob)."""
    r = ctx.stem * 0.55 if radius is None else radius
    return _ellipse(cx, cy, r, r)


def terminal_sheared(
    ctx: DesignContext,
    x0: float,
    y0: float,
    x1: float,
    y1: float,
    *,
    shear: float = 0.35,
) -> Outline:
    """Parallelogram terminal / cut end (sheared rectangle)."""
    t = abs(y1 - y0) if abs(y1 - y0) > 1e-9 else ctx.stem
    s = shear * t
    b = PathBuilder()
    b.moveTo(x0 + s, y0)
    b.lineTo(x1 + s, y0)
    b.lineTo(x1 - s, y1)
    b.lineTo(x0 - s, y1)
    b.closePath()
    return b.build()


def serif_bracket(
    ctx: DesignContext,
    x_stem: float,
    y: float,
    *,
    side: str = "left",
    length: float | None = None,
    thickness: float | None = None,
) -> Outline:
    """Simple bracket serif stub (rectangular + slight bracket curve).

    Enough for agents to attach serifs while iterating; not a full serif
    family. ``side`` is ``\"left\"`` or ``\"right\"`` relative to the stem face.
    """
    length = ctx.stem * 1.1 if length is None else length
    thickness = ctx.thin * 0.55 if thickness is None else thickness
    if side == "left":
        x0, x1 = x_stem - length, x_stem
    elif side == "right":
        x0, x1 = x_stem, x_stem + length
    else:
        raise ValueError("side must be 'left' or 'right'")
    # Mild bracket: outer corner rounded toward the stem.
    r = min(ctx.join_radius * 0.5, thickness * 0.8, length * 0.4)
    return rounded_rect(ctx, x0, y, x1, y + thickness, radius=r)


def ink_trap(
    ctx: DesignContext,
    apex_x: float,
    apex_y: float,
    *,
    depth: float | None = None,
    opening_deg: float = 30.0,
    bisector_deg: float = 270.0,
    size: float | None = None,
) -> Outline:
    """Wedge-shaped ink-trap / crotch opener (tip at the sharp corner).

    The tip sits on the outline apex. The base is ``depth`` units into the
    black along ``bisector_deg`` (0° = +x, 90° = +y). ``opening_deg`` is the
    full apex angle of the wedge; ``size`` optionally overrides the base
    half-width (defaults to ``depth * tan(opening/2)``).

    Subtract this outline from a solid (boolean difference) to open a crotch
    or relieve a sharp internal angle. Parameters apply to any sharp join —
    not letter-specific beauty hacks.
    """
    d = 12.0 if depth is None else depth
    if d <= 0:
        raise ValueError(f"depth must be positive, got {d!r}")
    if opening_deg <= 0 or opening_deg >= 180:
        raise ValueError(f"opening_deg must be in (0, 180), got {opening_deg!r}")
    half_open = math.radians(opening_deg / 2.0)
    base_half = (d * math.tan(half_open)) if size is None else float(size)
    if base_half <= 0:
        raise ValueError(f"size must be positive, got {base_half!r}")
    rad = math.radians(bisector_deg)
    bx, by = math.cos(rad), math.sin(rad)
    # Perpendicular to bisector for the base span
    px, py = -by, bx
    base_cx = apex_x + bx * d
    base_cy = apex_y + by * d
    return wedge(
        ctx,
        apex_x,
        apex_y,
        base_cx - px * base_half,
        base_cy - py * base_half,
        base_cx + px * base_half,
        base_cy + py * base_half,
    )


def crotch_opener(
    ctx: DesignContext,
    apex_x: float,
    apex_y: float,
    left_leg_deg: float,
    right_leg_deg: float,
    *,
    depth: float | None = None,
    size: float | None = None,
) -> Outline:
    """Ink-trap wedge aimed into a crotch defined by two outgoing leg angles.

    ``left_leg_deg`` / ``right_leg_deg`` are absolute bearings of the two edges
    leaving the apex (into the black legs). The bisector points into the
    crotch opening (white) flipped 180° so the wedge cuts into the join.
    Opening angle is the smaller angle between the legs.
    """
    # Unit vectors along legs
    la = math.radians(left_leg_deg)
    ra = math.radians(right_leg_deg)
    lx, ly = math.cos(la), math.sin(la)
    rx, ry = math.cos(ra), math.sin(ra)
    # Interior crotch direction = average of unit legs, then reverse into black
    mx, my = lx + rx, ly + ry
    mlen = math.hypot(mx, my)
    if mlen < 1e-9:
        # Opposite legs — bisector from cross product
        mx, my = -(ly + ry), lx + rx  # fallback
        mlen = math.hypot(mx, my) or 1.0
    mx, my = mx / mlen, my / mlen
    # Bisector into the *black* (opposite the crotch void)
    bis = math.degrees(math.atan2(-my, -mx))
    # Opening = angle between legs
    dot = max(-1.0, min(1.0, lx * rx + ly * ry))
    opening = math.degrees(math.acos(dot))
    # Use a modest fraction of the crotch angle so the trap is a relief notch
    trap_open = max(8.0, min(60.0, opening * 0.35))
    d = (ctx.stem * 0.22) if depth is None else depth
    return ink_trap(
        ctx,
        apex_x,
        apex_y,
        depth=d,
        opening_deg=trap_open,
        bisector_deg=bis,
        size=size,
    )


def apply_ink_trap(
    outline: Outline,
    trap: Outline,
) -> Outline:
    """Boolean-difference ``trap`` from ``outline`` (requires pathops)."""
    from typekernel.geo.boolean import boolean_op

    return boolean_op(outline, trap, "difference")

def crotch_join(
    left_leg: Outline,
    right_leg: Outline,
    ctx: DesignContext,
    *,
    apex: tuple[float, float] | None = None,
    depth: float | None = None,
    size: float | None = None,
) -> Outline:
    """Union two legs and open the crotch with an ink trap at their join.

    When ``apex`` is omitted, uses the midpoint of the two outlines' shared
    topmost tightest corner heuristic (bbox intersection center of tops).
    Prefer passing an explicit apex for synthetic fixtures.
    """
    from typekernel.geo.boolean import boolean_op
    from typekernel.geo.outline import bounds

    solid = boolean_op(left_leg, right_leg, "union")
    if apex is None:
        lb = bounds(left_leg)
        rb = bounds(right_leg)
        apex = ((lb[0] + lb[2] + rb[0] + rb[2]) / 4.0, max(lb[3], rb[3]))
    # Estimate leg bearings from apex toward each leg centroid
    def _centroid(o: Outline) -> tuple[float, float]:
        b = bounds(o)
        return ((b[0] + b[2]) / 2.0, (b[1] + b[3]) / 2.0)

    lc = _centroid(left_leg)
    rc = _centroid(right_leg)
    left_deg = math.degrees(math.atan2(lc[1] - apex[1], lc[0] - apex[0]))
    right_deg = math.degrees(math.atan2(rc[1] - apex[1], rc[0] - apex[0]))
    trap = crotch_opener(
        ctx, apex[0], apex[1], left_deg, right_deg, depth=depth, size=size
    )
    return boolean_op(solid, trap, "difference")




def shoulder(
    ctx: DesignContext,
    x_left: float,
    x_right: float,
    y_bottom: float,
    y_top: float,
    *,
    thickness: float | None = None,
    meet_fillet: float | None = None,
) -> Outline:
    """Alias for :func:`arch` — n/h/m shoulder trough."""
    return arch(
        ctx, x_left, x_right, y_bottom, y_top, thickness=thickness, meet_fillet=meet_fillet
    )


def shoulder_yoke(
    ctx: DesignContext,
    x_left: float,
    *,
    counter: float | None = None,
    stem_width: float | None = None,
    y_bottom: float = 0.0,
    stem_top: float | None = None,
    shoulder_top: float | None = None,
    join_y: float | None = None,
    crown_y: float | None = None,
    leg_top: float | None = None,
    inner_crown: float | None = None,
    kappa: float | None = None,
    branch_y: float | bool | None = None,
    written_feet: bool = True,
    inline_serifs: bool = False,
) -> Outline:
    """Continuous left-stem + shoulder + right-leg as **one** closed contour.

    Usage A ``n``-family body (see also :func:`h_yoke` / :func:`n_yoke`).
    ``shoulder_top`` (e.g. ``ctx.x_height`` on ``h``) is the upright shoulder
    spring when the left stem continues to a taller ``stem_top`` (ascender).
    ``branch_y`` matches :func:`double_shoulder_yoke`: ``True`` auto-picks
    ``≈ 0.58 * stem_top``; a float is absolute; ``None`` keeps the upright
    spring at ``shoulder_top`` or ``stem_top``. When branching, ``written_feet``
    adds entry kick + exit outstroke and softens the crotch.

    ``inline_serifs`` draws slab/bracket foot and cap serifs into the contour
    (upright only — branching + inline serifs stay on the private path).
    """
    from typekernel.geo.contour import reverse_contour, signed_area
    from typekernel.geo.path_helpers import KAPPA
    from typekernel.parts.italic_strokes import (
        emit_italic_branch_shoulder,
        emit_italic_entry_kick,
        emit_italic_exit_outstroke,
        italic_branch_radius,
    )

    t = ctx.stem if stem_width is None else stem_width
    if t <= 0:
        raise ValueError(f"stem_width must be positive, got {t!r}")
    w = (ctx.x_height * 0.42) if counter is None else counter
    if w <= 0:
        raise ValueError(f"counter must be positive, got {w!r}")
    top = ctx.x_height if stem_top is None else stem_top
    by = _resolve_branch_y(branch_y, stem_top=top, shoulder_top=shoulder_top)
    if inline_serifs and by is not None:
        raise ValueError("inline_serifs is unsupported with branch_y (italic serif)")
    upright_spring = top if shoulder_top is None else shoulder_top
    spring = by if by is not None else upright_spring
    upright_crown = (upright_spring + ctx.overshoot) if crown_y is None else crown_y
    drop = (top - by) if by is not None else 0.0
    crown = upright_crown - drop * 0.14
    if by is None and crown <= spring:
        crown = spring + max(ctx.overshoot, t * 0.08)
    join = (
        (upright_spring * (0.50 + 0.04 * ctx.roundness)) if join_y is None else join_y
    )
    if by is not None:
        join = min(join, by - t * 0.32)
    if inner_crown is None:
        upright_inner = upright_crown - t * (0.92 + 0.08 * ctx.contrast)
        inner_crown = upright_inner - drop * 0.16
    join = min(join, crown - t * 0.55)
    join = max(join, y_bottom + t * 0.35)
    k = (KAPPA * (0.92 + 0.28 * ctx.roundness)) if kappa is None else kappa
    l0 = x_left
    l1 = x_left + t
    r0 = l1 + w
    r1 = r0 + t
    mid = 0.5 * (l1 + r0)
    if leg_top is None:
        leg_top = upright_spring - t * 0.02
        if by is not None:
            leg_top = leg_top - (top - by) * 0.2
    o0 = (
        (l1, spring),
        (l1, spring + k * (crown - spring)),
        (mid - k * (mid - l1), crown),
        (mid, crown),
    )
    o1 = (
        (mid, crown),
        (mid + k * (r1 - mid), crown),
        (r1, leg_top + k * (crown - leg_top)),
        (r1, leg_top),
    )
    i0 = (
        (r0, join),
        (r0, join + k * (inner_crown - join)),
        (mid + k * (r0 - mid), inner_crown),
        (mid, inner_crown),
    )
    i1 = (
        (mid, inner_crown),
        (mid - k * (mid - l1), inner_crown),
        (l1, join + k * (inner_crown - join)),
        (l1, join),
    )
    serif = inline_serifs and ctx.style.serif in ("slab", "bracketed")
    is_h = shoulder_top is not None and abs(top - upright_spring) > 0.5
    slab_n_cap = serif and ctx.style.serif == "slab" and not is_h
    bracket_n_shoulder = (
        serif and ctx.style.serif == "bracketed" and not is_h
    )
    right_leg_top_cap = serif and (
        ctx.style.serif == "slab"
        or (ctx.style.serif == "bracketed" and is_h)
    )
    bracket_h_rect = serif and ctx.style.serif == "bracketed" and is_h

    b = PathBuilder()
    if by is not None and written_feet:
        emit_italic_entry_kick(b, l0, stem=t, left_top=top, y0=y_bottom)
        b.lineTo(l1, top)
    elif serif:
        from typekernel.parts.serifs import (
            inline_shoulder_left_cap_slab_path,
            inline_stem_cap_serif_path,
            inline_stem_cap_serif_path_slab_rect,
            inline_stem_foot_serif_path,
            inline_stem_foot_serif_path_right,
        )

        b.moveTo(l0, y_bottom)
        inline_stem_foot_serif_path(b, l0, y_bottom, ctx, t)
        b.lineTo(l0, top)
        if bracket_n_shoulder:
            inline_shoulder_left_cap_slab_path(b, l0, top, ctx, t)
        b.lineTo(l1, top)
        if is_h:
            scale = 1.0
            if bracket_h_rect:
                # Match control ``_n_bracketed_h_ascender_cap_thickness_scale`` loosely.
                scale = max(0.55, min(1.0, upright_spring / max(top, 1.0)))
            if bracket_h_rect:
                inline_stem_cap_serif_path_slab_rect(
                    b, l0, l1, top, ctx, t, thickness_scale=scale
                )
            else:
                inline_stem_cap_serif_path(b, l0, l1, top, ctx, t)
            b.lineTo(l1, spring)
        elif slab_n_cap:
            inline_stem_cap_serif_path(b, l0, l1, top, ctx, t)
    else:
        b.moveTo(l0, y_bottom)
        b.lineTo(l0, top)
        b.lineTo(l1, top)
    if by is not None:
        emit_italic_branch_shoulder(
            b,
            branch_x=l1,
            branch_y=by,
            shoulder0=o0,
            radius=italic_branch_radius(top, by),
        )
        b.curveTo(o1[1][0], o1[1][1], o1[2][0], o1[2][1], o1[3][0], o1[3][1])
    else:
        if (not serif) and shoulder_top is not None and abs(top - spring) > 0.5:
            b.lineTo(l1, spring)
        b.curveTo(o0[1][0], o0[1][1], o0[2][0], o0[2][1], o0[3][0], o0[3][1])
        if right_leg_top_cap:
            from fontTools.misc.bezierTools import splitCubicAtT

            # Split outer[1] at x-height (horizontal) via binary search on y.
            p0, p1, p2, p3 = (tuple(p) for p in o1)
            # Approximate t where y == upright_spring
            lo_t, hi_t = 0.0, 1.0
            for _ in range(24):
                mid_t = 0.5 * (lo_t + hi_t)
                _l, right = splitCubicAtT(p0, p1, p2, p3, mid_t)
                y_m = right[0][1]
                if y_m > upright_spring:
                    lo_t = mid_t
                else:
                    hi_t = mid_t
            left, right = splitCubicAtT(p0, p1, p2, p3, 0.5 * (lo_t + hi_t))
            lpts = [tuple(pt) for pt in left]
            rpts = [tuple(pt) for pt in right]
            b.curveTo(lpts[1][0], lpts[1][1], lpts[2][0], lpts[2][1], lpts[3][0], lpts[3][1])
            b.lineTo(r1, upright_spring)
            from typekernel.parts.serifs import (
                inline_stem_cap_serif_path,
                inline_stem_cap_serif_path_slab_rect,
            )

            if bracket_h_rect:
                scale = max(0.55, min(1.0, upright_spring / max(top, 1.0)))
                inline_stem_cap_serif_path_slab_rect(
                    b, r0, r1, upright_spring, ctx, t, thickness_scale=scale
                )
            else:
                inline_stem_cap_serif_path(b, r0, r1, upright_spring, ctx, t)
            b.lineTo(r1, rpts[3][1])
        else:
            b.curveTo(o1[1][0], o1[1][1], o1[2][0], o1[2][1], o1[3][0], o1[3][1])
    if by is not None and written_feet:
        emit_italic_exit_outstroke(b, r0, r1, stem=t)
    elif serif:
        from typekernel.parts.serifs import inline_stem_foot_serif_path_right

        b.lineTo(r1, y_bottom)
        inline_stem_foot_serif_path_right(b, r1, y_bottom, ctx, t)
        b.lineTo(r0, y_bottom)
    else:
        b.lineTo(r1, y_bottom)
        b.lineTo(r0, y_bottom)
    b.lineTo(r0, join)
    b.curveTo(i0[1][0], i0[1][1], i0[2][0], i0[2][1], i0[3][0], i0[3][1])
    b.curveTo(i1[1][0], i1[1][1], i1[2][0], i1[2][1], i1[3][0], i1[3][1])
    b.lineTo(l1, y_bottom)
    b.closePath()
    outline = b.build()
    c0 = outline.contours[0]
    if signed_area(c0) < 0:
        outline = Outline((reverse_contour(c0),))
    return outline



def n_yoke(
    ctx: DesignContext,
    x_left: float = 0.0,
    *,
    counter: float | None = None,
    stem_width: float | None = None,
    y_bottom: float = 0.0,
    stem_top: float | None = None,
    shoulder_top: float | None = None,
    join_y: float | None = None,
    crown_y: float | None = None,
    leg_top: float | None = None,
    inner_crown: float | None = None,
    kappa: float | None = None,
    branch_y: float | bool | None = None,
    written_feet: bool = True,
    inline_serifs: bool = False,
) -> Outline:
    """Public Usage A ``n`` body — alias of :func:`shoulder_yoke`.

    ``branch_y=True`` (or a float) yields the written italic branching recipe.
    ``inline_serifs`` draws upright slab/bracket feet and caps into the contour.
    """
    return shoulder_yoke(
        ctx,
        x_left,
        counter=counter,
        stem_width=stem_width,
        y_bottom=y_bottom,
        stem_top=stem_top,
        shoulder_top=shoulder_top,
        join_y=join_y,
        crown_y=crown_y,
        leg_top=leg_top,
        inner_crown=inner_crown,
        kappa=kappa,
        branch_y=branch_y,
        written_feet=written_feet,
        inline_serifs=inline_serifs,
    )


def h_yoke(
    ctx: DesignContext,
    x_left: float = 0.0,
    *,
    counter: float | None = None,
    stem_width: float | None = None,
    y_bottom: float = 0.0,
    stem_top: float | None = None,
    shoulder_top: float | None = None,
    join_y: float | None = None,
    crown_y: float | None = None,
    leg_top: float | None = None,
    inner_crown: float | None = None,
    kappa: float | None = None,
    branch_y: float | bool | None = None,
    written_feet: bool = True,
    inline_serifs: bool = False,
) -> Outline:
    """Public Usage A ``h`` body — :func:`shoulder_yoke` with ascender stem.

    Default ``stem_top`` is ``ctx.ascender``; shoulder springs at
    ``shoulder_top`` (default ``ctx.x_height``), matching ``build_h``.
    ``inline_serifs`` draws upright slab/bracket feet and caps into the contour.
    """
    top = ctx.ascender if stem_top is None else stem_top
    sh = ctx.x_height if shoulder_top is None else shoulder_top
    return shoulder_yoke(
        ctx,
        x_left,
        counter=counter,
        stem_width=stem_width,
        y_bottom=y_bottom,
        stem_top=top,
        shoulder_top=sh,
        join_y=join_y,
        crown_y=crown_y,
        leg_top=leg_top,
        inner_crown=inner_crown,
        kappa=kappa,
        branch_y=branch_y,
        written_feet=written_feet,
        inline_serifs=inline_serifs,
    )


def _resolve_branch_y(
    branch_y: float | bool | None,
    *,
    stem_top: float,
    shoulder_top: float | None = None,
) -> float | None:
    """``True`` → auto mid-stem branch; ``float`` → absolute; ``None``/``False`` → upright.

    When ``shoulder_top`` is set and ``stem_top`` is an ascender (``h``), ``True``
    matches control ``_italic_branch_y``.
    """
    if branch_y is None or branch_y is False:
        return None
    if branch_y is True:
        if shoulder_top is not None and stem_top > shoulder_top + 1.0:
            return shoulder_top + (stem_top - shoulder_top) * 0.38
        return stem_top * 0.58
    by = float(branch_y)
    if by <= 0 or by >= stem_top:
        raise ValueError(f"branch_y must be in (0, stem_top), got {by!r}")
    return by


def double_shoulder_yoke(
    ctx: DesignContext,
    x_left: float,
    *,
    counter: float | None = None,
    stem_width: float | None = None,
    y_bottom: float = 0.0,
    stem_top: float | None = None,
    join_y: float | None = None,
    crown_y: float | None = None,
    leg_top: float | None = None,
    inner_crown: float | None = None,
    kappa: float | None = None,
    counter_scale: float = 0.92,
    branch_y: float | bool | None = None,
    written_feet: bool = True,
) -> Outline:
    """Continuous ``m`` body: two shoulders sharing a middle stem (one contour).

    No boolean union. ``branch_y`` enables italic left-stem branching
    (``True`` → ``≈ 0.58 * stem_top``; float → absolute). Middle crotch shelf
    stays at ``stem_top``; shoulders spring from ``branch_y``. ``written_feet``
    adds entry kick + exit outstroke and softens the branch crotch.
    """
    from fontTools.misc.bezierTools import splitCubic

    from typekernel.geo.contour import reverse_contour, signed_area
    from typekernel.geo.path_helpers import KAPPA
    from typekernel.parts.italic_strokes import (
        emit_italic_branch_shoulder,
        emit_italic_entry_kick,
        emit_italic_exit_outstroke,
        italic_branch_radius,
    )

    if counter_scale <= 0:
        raise ValueError(f"counter_scale must be positive, got {counter_scale!r}")
    t = ctx.stem if stem_width is None else stem_width
    if t <= 0:
        raise ValueError(f"stem_width must be positive, got {t!r}")
    base_w = (ctx.x_height * 0.42) if counter is None else counter
    w = base_w * counter_scale
    if w <= 0:
        raise ValueError(f"counter must be positive, got {w!r}")
    top = ctx.x_height if stem_top is None else stem_top
    by = _resolve_branch_y(branch_y, stem_top=top)
    # Shoulder spring height (branch or upright crown spring).
    spring = by if by is not None else top
    upright_crown = (top + ctx.overshoot) if crown_y is None else crown_y
    drop = (top - by) if by is not None else 0.0
    crown = upright_crown - drop * 0.14
    if by is None and crown <= spring:
        crown = spring + max(ctx.overshoot, t * 0.08)
    join = (top * (0.50 + 0.04 * ctx.roundness)) if join_y is None else join_y
    if by is not None:
        join = min(join, by - t * 0.32)
    if inner_crown is None:
        # double_shoulder upright uses a shallower inner than n (0.55 vs 0.92).
        upright_inner = upright_crown - t * (0.55 + 0.08 * ctx.contrast)
        inner_crown = upright_inner - drop * 0.16
    # Lift inner crown toward spring so middle crotch shelf can meet at stem_top
    # (upright only — italic branch spring is mid-stem).
    if by is None:
        inner_crown = min(max(inner_crown, spring), crown - t * 0.06)
    else:
        inner_crown = min(inner_crown, crown - t * 0.06)
    join = min(join, inner_crown - t * 0.15)
    join = max(join, y_bottom + t * 0.35)
    k = (KAPPA * (0.92 + 0.28 * ctx.roundness)) if kappa is None else kappa

    Cubic = tuple[
        tuple[float, float], tuple[float, float], tuple[float, float], tuple[float, float]
    ]

    def _shoulder_at(
        x0: float,
    ) -> tuple[float, float, float, float, Cubic, Cubic, Cubic, Cubic]:
        l0, l1 = x0, x0 + t
        r0, r1 = x0 + t + w, x0 + t + w + t
        mid = 0.5 * (l1 + r0)
        lt = leg_top
        if lt is None:
            lt = top - t * 0.02
            if by is not None:
                lt = lt - (top - by) * 0.2
        o0 = (
            (l1, spring),
            (l1, spring + k * (crown - spring)),
            (mid - k * (mid - l1), crown),
            (mid, crown),
        )
        o1 = (
            (mid, crown),
            (mid + k * (r1 - mid), crown),
            (r1, lt + k * (crown - lt)),
            (r1, lt),
        )
        i0 = (
            (r0, join),
            (r0, join + k * (inner_crown - join)),
            (mid + k * (r0 - mid), inner_crown),
            (mid, inner_crown),
        )
        i1 = (
            (mid, inner_crown),
            (mid - k * (mid - l1), inner_crown),
            (l1, join + k * (inner_crown - join)),
            (l1, join),
        )
        return l0, l1, r0, r1, o0, o1, i0, i1

    l0, l1, r0_mid, r1_mid, o0a, o1a, i0a, i1a = _shoulder_at(x_left)
    _l0b, l1b, r0, r1, o0b, o1b, i0b, i1b = _shoulder_at(r0_mid)

    def _curve(b: PathBuilder, c: Cubic) -> None:
        b.curveTo(c[1][0], c[1][1], c[2][0], c[2][1], c[3][0], c[3][1])

    def _split_y(c: Cubic, y: float) -> tuple[Cubic, Cubic] | None:
        pieces = splitCubic(*c, y, True)
        if len(pieces) != 2:
            return None
        return (tuple(pieces[0]), tuple(pieces[1]))

    b = PathBuilder()
    if by is not None and written_feet:
        emit_italic_entry_kick(b, l0, stem=t, left_top=top, y0=y_bottom)
    else:
        b.moveTo(l0, y_bottom)
        b.lineTo(l0, top)
    b.lineTo(l1, top)
    if by is not None:
        emit_italic_branch_shoulder(
            b,
            branch_x=l1,
            branch_y=by,
            shoulder0=o0a,
            radius=italic_branch_radius(top, by),
        )
    else:
        _curve(b, o0a)
    # Middle crotch shelf at full stem_top (m_from_n recipe), not at branch_y.
    split1 = _split_y(o1a, top)
    split2 = _split_y(o0b, top)
    if split1 is not None and split2 is not None:
        _curve(b, split1[0])
        _curve(b, split2[1])
    else:
        _curve(b, o1a)
        _curve(b, o0b)
    _curve(b, o1b)
    if by is not None and written_feet:
        emit_italic_exit_outstroke(b, r0, r1, stem=t)
    else:
        b.lineTo(r1, y_bottom)
        b.lineTo(r0, y_bottom)
    b.lineTo(r0, join)
    isplit2 = _split_y(i0b, top)
    isplit1 = _split_y(i1a, top)
    if isplit2 is not None:
        _curve(b, isplit2[0])
    else:
        _curve(b, i0b)
    if isplit1 is not None and isplit2 is not None:
        b.lineTo(r1_mid, top)
        b.lineTo(l1b, top)
        _curve(b, isplit1[1])
    else:
        _curve(b, i1b)
    b.lineTo(l1b, y_bottom)
    b.lineTo(r0_mid, y_bottom)
    b.lineTo(r0_mid, join)
    _curve(b, i0a)
    if isplit1 is not None:
        _curve(b, isplit1[0])
    else:
        _curve(b, i1a)
    b.lineTo(l1, y_bottom)
    b.closePath()
    outline = b.build()
    c0 = outline.contours[0]
    if signed_area(c0) < 0:
        outline = Outline((reverse_contour(c0),))
    return outline


def u_yoke(
    ctx: DesignContext,
    x_left: float,
    *,
    counter: float | None = None,
    stem_width: float | None = None,
    y_bottom: float = 0.0,
    stem_top: float | None = None,
    join_y: float | None = None,
    crown_y: float | None = None,
    leg_top: float | None = None,
    inner_crown: float | None = None,
    kappa: float | None = None,
    branch_y: float | bool | None = None,
    foot_bulge: float | None = None,
    written_feet: bool = True,
) -> Outline:
    """Continuous ``u`` body: bowl on the left, upright stem on the right.

    One contour, no boolean. Geometry mirrors :func:`shoulder_yoke` across the
    advance (``n`` flipped). ``branch_y`` (``True`` / float) springs the bowl
    from the **right** stem mid-height (italic ``u``). Unlike left-stem
    ``n``/``h`` emit fillets, the mirrored crotch uses sharp branch +
    :func:`soften_stem_branch` so VF wght×ital segment counts stay stable.
    When branching, ``written_feet`` adds the mirrored entry kick (right stem)
    and exit outstroke (left bowl) **if** ``foot_bulge`` is zero — matching
    control ``_u_branching_outline``. Low roundness keeps the baseline toe
    instead so VF upright/italic segment kinds stay aligned.
    """
    from typekernel.geo.contour import reverse_contour, signed_area
    from typekernel.geo.path_helpers import KAPPA
    from typekernel.parts.italic_strokes import italic_kick_dims

    t = ctx.stem if stem_width is None else stem_width
    if t <= 0:
        raise ValueError(f"stem_width must be positive, got {t!r}")
    w = (ctx.x_height * 0.42) if counter is None else counter
    if w <= 0:
        raise ValueError(f"counter must be positive, got {w!r}")
    top = ctx.x_height if stem_top is None else stem_top
    by = _resolve_branch_y(branch_y, stem_top=top)
    # Upright shoulder band is stem_top (x-height); branch retune matches n_yoke.
    upright_spring = top
    spring = by if by is not None else upright_spring
    upright_crown = (upright_spring + ctx.overshoot) if crown_y is None else crown_y
    drop = (top - by) if by is not None else 0.0
    crown = upright_crown - drop * 0.14
    if by is None and crown <= spring:
        crown = spring + max(ctx.overshoot, t * 0.08)
    join = (
        (upright_spring * (0.50 + 0.04 * ctx.roundness)) if join_y is None else join_y
    )
    if by is not None:
        join = min(join, by - t * 0.32)
    if inner_crown is None:
        upright_inner = upright_crown - t * (0.92 + 0.08 * ctx.contrast)
        inner_crown = upright_inner - drop * 0.16
    join = min(join, crown - t * 0.55)
    join = max(join, y_bottom + t * 0.35)
    k = (KAPPA * (0.92 + 0.28 * ctx.roundness)) if kappa is None else kappa
    width = 2.0 * t + w
    cx = x_left + width / 2.0
    l0, l1 = 0.0, t
    r0, r1 = t + w, width
    mid = 0.5 * (l1 + r0)

    if leg_top is None:
        leg_top = upright_spring - t * 0.02
        if by is not None:
            leg_top = leg_top - drop * 0.2
    o0 = (
        (l1, spring),
        (l1, spring + k * (crown - spring)),
        (mid - k * (mid - l1), crown),
        (mid, crown),
    )
    o1 = (
        (mid, crown),
        (mid + k * (r1 - mid), crown),
        (r1, leg_top + k * (crown - leg_top)),
        (r1, leg_top),
    )
    i0 = (
        (r0, join),
        (r0, join + k * (inner_crown - join)),
        (mid + k * (r0 - mid), inner_crown),
        (mid, inner_crown),
    )
    i1 = (
        (mid, inner_crown),
        (mid - k * (mid - l1), inner_crown),
        (l1, join + k * (inner_crown - join)),
        (l1, join),
    )

    def mx(x: float) -> float:
        return 2.0 * cx - x

    def mp(p: tuple[float, float]) -> tuple[float, float]:
        return (mx(p[0]), p[1])

    def mc(
        c: tuple[
            tuple[float, float],
            tuple[float, float],
            tuple[float, float],
            tuple[float, float],
        ],
    ) -> tuple[
        tuple[float, float],
        tuple[float, float],
        tuple[float, float],
        tuple[float, float],
    ]:
        return (mp(c[0]), mp(c[1]), mp(c[2]), mp(c[3]))

    ro, ri = mx(l0), mx(l1)
    lo, li = mx(r1), mx(r0)
    bulge = foot_bulge
    if bulge is None:
        # Match control ``_u_foot_bulge``: zero when roundness ≥ 0.35.
        bulge = 0.0 if ctx.roundness >= 0.35 else max(t * 0.08, 4.0)
    # Private italic ``u`` uses written kicks only when bulge is zero; low
    # roundness keeps the baseline toe and skips kicks so VF upright/italic
    # segment kinds stay aligned.
    use_feet = by is not None and written_feet and bulge <= 0.0
    shelf = t * 0.20

    b = PathBuilder()
    if use_feet:
        # Mirrored entry kick: n's left-stem kick → u right-stem outer.
        dx, dy = italic_kick_dims(t)
        rise = max(2.0, top - y_bottom)
        dy = min(dy, max(2.0, rise * 0.22))
        b.moveTo(ro - dx, y_bottom)
        b.curveTo(ro - dx * 0.35, y_bottom, ro, y_bottom + dy * 0.45, ro, y_bottom + dy)
        b.lineTo(ro, top)
    else:
        b.moveTo(ro, y_bottom)
        b.lineTo(ro, top)
    b.lineTo(ri, top)
    if by is not None:
        b.lineTo(ri, by)
    mo0, mo1 = mc(o0), mc(o1)
    b.curveTo(mo0[1][0], mo0[1][1], mo0[2][0], mo0[2][1], mo0[3][0], mo0[3][1])
    b.curveTo(mo1[1][0], mo1[1][1], mo1[2][0], mo1[2][1], mo1[3][0], mo1[3][1])
    if use_feet:
        # Mirrored exit outstroke: n's right-leg exit → u left bowl.
        dx, dy = italic_kick_dims(t)
        b.lineTo(lo, dy)
        b.curveTo(lo, dy * 0.45, lo + dx * 0.35, y_bottom, lo + dx, y_bottom)
        b.lineTo(li, y_bottom)
    elif bulge <= 0.0:
        b.lineTo(lo, y_bottom)
        b.lineTo(li, y_bottom)
    else:
        b.lineTo(lo, y_bottom)
        x_shelf = li - shelf
        b.curveTo(lo, y_bottom - bulge, x_shelf - bulge * 0.5, y_bottom, x_shelf, y_bottom)
        b.lineTo(li, y_bottom)
    b.lineTo(li, join)
    mi0, mi1 = mc(i0), mc(i1)
    b.curveTo(mi0[1][0], mi0[1][1], mi0[2][0], mi0[2][1], mi0[3][0], mi0[3][1])
    b.curveTo(mi1[1][0], mi1[1][1], mi1[2][0], mi1[2][1], mi1[3][0], mi1[3][1])
    b.lineTo(ri, y_bottom)
    b.closePath()
    outline = b.build()
    c0 = outline.contours[0]
    if signed_area(c0) < 0:
        outline = Outline((reverse_contour(c0),))
    if by is not None:
        outline = soften_stem_branch(
            outline,
            stem_x=ri,
            branch_y=by,
            stem=t,
            stem_top=top,
        )
        c0 = outline.contours[0]
        if signed_area(c0) < 0:
            outline = Outline((reverse_contour(c0),))
    return outline



def soften_stem_branch(

    outline: Outline,
    *,
    stem_x: float,
    branch_y: float,
    stem: float,
    stem_top: float,
    tension: float = 0.95,
) -> Outline:
    """Blend the stem→shoulder crotch at ``(stem_x, branch_y)`` on one outline.

    Use after drawing a sharp branch (line into shoulder cubic) — typical
    italic ``n``/``h``/``m``/``r`` topology. Selects only the line→curve join
    nearest the branch point so other corners stay put. Radius scales from
    the branch drop (``stem_top - branch_y``), not stem weight, so wght
    ladders keep a stable segment recipe.

    Does **not** require boolean. Part-exit quality helper for written italic.
    """
    from typekernel.geo.extrema import outline_with_axis_extrema_on_curve
    from typekernel.geo.joins import _is_line, _seg_end, blend_corners

    drop = max(0.0, stem_top - branch_y)
    radius = max(2.0, drop * 0.18)
    tol = max(6.0, stem * 0.15)

    def select(angle: float, a: object, b: object) -> bool:
        if angle < 0.5:
            return False
        if not (_is_line(a) and not _is_line(b)):  # type: ignore[arg-type]
            return False
        pt = _seg_end(a)  # type: ignore[arg-type]
        return abs(pt.y - branch_y) <= tol and abs(pt.x - stem_x) <= tol

    blended = blend_corners(outline, radius, select=select, tension=tension)
    return outline_with_axis_extrema_on_curve(blended)


def r_yoke(
    ctx: DesignContext,
    x_left: float = 0.0,
    *,
    arm: float = 0.55,
    counter: float | None = None,
    stem_width: float | None = None,
    y_bottom: float = 0.0,
    stem_top: float | None = None,
    join_y: float | None = None,
    crown_y: float | None = None,
    leg_top: float | None = None,
    inner_crown: float | None = None,
    kappa: float | None = None,
    branch_y: float | bool | None = None,
    written_feet: bool = True,
) -> Outline:
    """Continuous ``r`` body: left stem + truncated shoulder (one contour).

    ``arm`` in ``(0, 1)`` cuts the shoulder short of a full ``n`` right leg —
    Usage A open-arm ``r`` without boolean kit-of-parts. ``branch_y`` matches
    :func:`shoulder_yoke` (italic branch + crotch soften + optional written
    entry). The arm tip is a flat vertical cut at the truncate x.
    """
    from fontTools.misc.bezierTools import splitCubic

    from typekernel.geo.contour import reverse_contour, signed_area
    from typekernel.geo.path_helpers import KAPPA
    from typekernel.parts.italic_strokes import (
        emit_italic_branch_shoulder,
        emit_italic_entry_kick,
        italic_arm_terminal_cubic,
        italic_branch_radius,
    )

    if not 0.0 < arm < 1.0:
        raise ValueError(f"arm must be in (0, 1), got {arm!r}")
    t = ctx.stem if stem_width is None else stem_width
    if t <= 0:
        raise ValueError(f"stem_width must be positive, got {t!r}")
    w = (ctx.x_height * 0.42) if counter is None else counter
    if w <= 0:
        raise ValueError(f"counter must be positive, got {w!r}")
    top = ctx.x_height if stem_top is None else stem_top
    by = _resolve_branch_y(branch_y, stem_top=top)
    spring = by if by is not None else top
    upright_crown = (top + ctx.overshoot) if crown_y is None else crown_y
    drop = (top - by) if by is not None else 0.0
    crown = upright_crown - drop * 0.14
    if by is None and crown <= spring:
        crown = spring + max(ctx.overshoot, t * 0.08)
    join = (top * (0.50 + 0.04 * ctx.roundness)) if join_y is None else join_y
    if by is not None:
        join = min(join, by - t * 0.32)

    if inner_crown is None:
        upright_inner = upright_crown - t * (0.92 + 0.08 * ctx.contrast)
        inner_crown = upright_inner - drop * 0.16
    join = min(join, crown - t * 0.55)
    join = max(join, y_bottom + t * 0.35)
    k = (KAPPA * (0.92 + 0.28 * ctx.roundness)) if kappa is None else kappa
    l0 = x_left
    l1 = x_left + t
    r0 = l1 + w
    r1 = r0 + t
    mid = 0.5 * (l1 + r0)

    if leg_top is None:
        leg_top = top - t * 0.02
        if by is not None:
            leg_top = leg_top - (top - by) * 0.2
    o0 = (
        (l1, spring),
        (l1, spring + k * (crown - spring)),
        (mid - k * (mid - l1), crown),
        (mid, crown),
    )
    o1 = (
        (mid, crown),
        (mid + k * (r1 - mid), crown),
        (r1, leg_top + k * (crown - leg_top)),
        (r1, leg_top),
    )
    i0 = (
        (r0, join),
        (r0, join + k * (inner_crown - join)),
        (mid + k * (r0 - mid), inner_crown),
        (mid, inner_crown),
    )
    i1 = (
        (mid, inner_crown),
        (mid - k * (mid - l1), inner_crown),
        (l1, join + k * (inner_crown - join)),
        (l1, join),
    )
    x_t = mid + arm * (r0 - mid)
    Cubic = tuple[
        tuple[float, float],
        tuple[float, float],
        tuple[float, float],
        tuple[float, float],
    ]

    def _split_x(c: Cubic, x: float) -> tuple[Cubic, Cubic] | None:
        pieces = splitCubic(*c, x, False)
        if len(pieces) != 2:
            return None
        return (tuple(pieces[0]), tuple(pieces[1]))

    outer_cut = _split_x(o1, x_t)
    inner_cut = _split_x(i0, x_t)
    if outer_cut is None or inner_cut is None:
        raise ValueError("shoulder does not cross the r arm truncate")
    outer_arm = outer_cut[0]
    inner_arm = inner_cut[1]

    def _curve(b: PathBuilder, c: Cubic) -> None:
        b.curveTo(c[1][0], c[1][1], c[2][0], c[2][1], c[3][0], c[3][1])

    b = PathBuilder()
    if by is not None and written_feet:
        emit_italic_entry_kick(b, l0, stem=t, left_top=top, y0=y_bottom)
    else:
        b.moveTo(l0, y_bottom)
        b.lineTo(l0, top)
    b.lineTo(l1, top)
    if by is not None:
        emit_italic_branch_shoulder(
            b,
            branch_x=l1,
            branch_y=by,
            shoulder0=o0,
            radius=italic_branch_radius(top, by),
        )
    else:
        _curve(b, o0)
    _curve(b, outer_arm)
    if by is not None:
        _curve(
            b,
            italic_arm_terminal_cubic(outer_arm[3], inner_arm[0], stem=t),
        )
    else:
        # Flat vertical tip at truncate x.
        b.lineTo(inner_arm[0][0], inner_arm[0][1])
    _curve(b, inner_arm)
    _curve(b, i1)
    b.lineTo(l1, y_bottom)
    b.closePath()
    outline = b.build()
    c0 = outline.contours[0]
    if signed_area(c0) < 0:
        outline = Outline((reverse_contour(c0),))
    return outline



def smooth_hook(
    ctx: DesignContext,
    x_right: float,
    y_top: float,
    y_bottom: float,
    *,
    radius: float | None = None,
    tail: float | None = None,
    width: float | None = None,
) -> Outline:
    """Descending stem that turns left in one continuous quarter arc (``j``).

    Stem → arc → horizontal tail with tangent-continuous joins (no polyline
    facets). ``x_right`` is the stem's right edge, ``y_bottom`` the outer
    bottom of the hook, ``tail`` how far the terminal reaches left of the
    arc. Ends are flat terminals.
    """
    t = ctx.stem if width is None else width
    r = max(t * 1.15, (y_top - y_bottom) * 0.30) if radius is None else radius
    tail_len = r * 0.55 if tail is None else tail
    left = x_right - t
    cx, cy = x_right - r, y_bottom + r
    b = PathBuilder()
    b.moveTo(left, y_top)
    b.lineTo(x_right, y_top)
    b.lineTo(x_right, cy)
    b.arcTo(cx, cy, r, r, -90.0, start_angle_deg=0.0)
    b.lineTo(cx - tail_len, y_bottom)
    b.lineTo(cx - tail_len, y_bottom + t)
    b.lineTo(cx, y_bottom + t)
    b.arcTo(cx, cy, r - t, r - t, 0.0, start_angle_deg=-90.0)
    b.lineTo(left, y_top)
    b.closePath()
    return b.build()
