"""Curve anatomy parts: arch, bowl, bowl_join, open_bowl, spine (target §4.3)."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Literal

from typekernel.draw import (
    Drawing,
    Fragment,
    Measure,
    Writer,
    superellipse_quarter,
    tensioned_arc,
)
from typekernel.geo.point import Point

__all__ = [
    "BarSpec",
    "arch",
    "bowl",
    "bowl_join",
    "open_bowl",
    "spine",
]

PointLike = Point | tuple[float, float]
Side = Literal["left", "right"]


def _as_point(p: PointLike) -> Point:
    if isinstance(p, Point):
        return p
    return Point(float(p[0]), float(p[1]))


def _with_measures(drawing: Drawing, *measures: Measure) -> Drawing:
    return Drawing(
        drawing.contours,
        drawing.roles,
        drawing.nodes,
        drawing.slots,
        measures,
    )


def _ccw_unit(dx: float, dy: float) -> tuple[float, float]:
    length = math.hypot(dx, dy) or 1.0
    return (-dy / length, dx / length)


def _superellipse_x_at_y_frac(rx: float, y_frac: float, exp: float) -> float:
    t = min(abs(y_frac), 1.0)
    return float(float(rx) * (max(1.0 - t**float(exp), 0.0)) ** (1.0 / float(exp)))


def _arch_span(
    x0: float,
    y0: float,
    x1: float,
    y1: float,
    crown_y: float,
    *,
    crown_x: float | None = None,
    tension: float,
) -> Fragment:
    mid_x = float(crown_x) if crown_x is not None else (x0 + x1) / 2.0
    sx = 1.0 if x1 >= x0 else -1.0
    left = tensioned_arc(
        (x0, y0), (sx, 0.0), (mid_x, crown_y), (sx, 0.0), tension=tension
    )
    right = tensioned_arc(
        (mid_x, crown_y), (sx, 0.0), (x1, y1), (sx, 0.0), tension=tension
    )
    return Fragment(left.segments + right.segments)


def arch(
    stem_face_x: float,
    right_outer_x: float,
    *,
    height: float,
    thick: float,
    thin: float,
    join_depth: float,
    tension: float,
    crown_shift: float = 0.0,
    overshoot: float = 0.0,
    name: str = "arch",
) -> Drawing:
    """Closed shoulder trough (overlap-ready) between left stem face and right x.

    Outer path leaves the stem face at ``y = height - join_depth``; crown y is in
    ``[height, height + overshoot]``; vertical distance at the stem join aims at
    ``thin``.
    """
    if float(thick) <= 0 or float(thin) <= 0:
        raise ValueError("thick and thin must be positive")
    if float(join_depth) < 0:
        raise ValueError("join_depth must be >= 0")
    if float(right_outer_x) <= float(stem_face_x):
        raise ValueError("right_outer_x must be greater than stem_face_x")

    x_left = float(stem_face_x)
    x_right = float(right_outer_x)
    y_top = float(height) - float(join_depth)
    # Outer crown at height..height+overshoot (join_depth drops the join below height).
    outer_crown = float(height) + float(overshoot)
    # Inner path sits ``thin`` below the join at the stem; trough depth ~ thick.
    y_bot = y_top - float(thin)
    inner_crown = y_bot - max(float(thick) - float(thin), float(thin) * 0.2)
    crown_x = 0.5 * (x_left + x_right) + float(crown_shift)

    outer = _arch_span(
        x_left, y_top, x_right, y_top, outer_crown, crown_x=crown_x, tension=float(tension)
    )
    inner = _arch_span(
        x_right, y_bot, x_left, y_bot, inner_crown, crown_x=crown_x, tension=float(tension)
    )
    drawing = (
        Writer()
        .start((x_left, y_bot))
        .corner(f"{name}.entry")
        .line((x_left, y_top))
        .corner("join.crotch.l")
        .fragment(outer)
        .corner("join.crotch.r")
        .line((x_right, y_bot))
        .corner(f"{name}.exit")
        .fragment(inner)
        .close()
        .build()
    )
    # Crown height is carried on the join.l Measure meta via expected on a height
    # measure keyed to join.r (highest tagged corner on the outer path start/end).
    measures = (
        Measure(
            kind="thin",
            a="join.crotch.l",
            b=f"{name}.entry",
            expected=float(thin),
            direction_deg=90.0,
        ),
        Measure(kind="height", a="join.crotch.l", expected=float(outer_crown)),
        Measure(kind="crotch", a="join.crotch.l", expected=float(join_depth)),
    )
    return _with_measures(drawing, *measures)


def bowl(
    center: PointLike,
    rx: float,
    ry: float,
    *,
    thick: float,
    thin: float,
    stress_deg: float = 0.0,
    exponent: float = 2.0,
    overshoot: float = 0.0,
    name: str = "bowl",
) -> Drawing:
    """Superellipse ring: ink outer + counter hole."""
    if float(thick) <= 0 or float(thin) <= 0:
        raise ValueError("thick and thin must be positive")
    if float(rx) <= float(thick) or float(ry) <= 0:
        raise ValueError("rx/ry too small for thickness")
    c = _as_point(center)
    outer_rx = float(rx)
    outer_ry = float(ry) + float(overshoot)
    # Stress rotates which axis is thick/thin for the *inner* inset.
    ang = math.radians(float(stress_deg))
    # Axis-aligned inset; contracts measure along stress axes via ray spans.
    # When stress_deg ≈ 0: horizontal thick, vertical thin.
    inner_rx = max(outer_rx - float(thick), 1.0)
    inner_ry = max(outer_ry - float(thin), 1.0)
    if abs(stress_deg) > 1e-6:
        # Blend inset radii toward swapped roles as stress approaches 90°.
        t = abs(math.sin(ang))
        hx, hy = float(thick), float(thin)
        # At 90°, horizontal gets thin and vertical gets thick.
        h_inset = hx * (1.0 - t) + hy * t
        v_inset = hy * (1.0 - t) + hx * t
        inner_rx = max(outer_rx - h_inset, 1.0)
        inner_ry = max(outer_ry - v_inset, 1.0)

    def _ring(rx_: float, ry_: float, *, counter: bool, prefix: str) -> Drawing:
        frags = [
            superellipse_quarter(c, rx_, ry_, q, exponent=float(exponent))
            for q in range(4)
        ]
        w = Writer().start(frags[0].start)
        w.node(f"{prefix}.stress")
        for frag in frags:
            w.fragment(frag)
        return w.close(role="counter" if counter else "ink").build()

    outer = _ring(outer_rx, outer_ry, counter=False, prefix=f"{name}.o")
    inner = _ring(inner_rx, inner_ry, counter=True, prefix=f"{name}.i")
    combined = outer + inner
    measures = (
        Measure(
            kind="stem",
            a=f"{name}.o.stress",
            b=f"{name}.i.stress",
            expected=float(thick),
            direction_deg=float(stress_deg),
        ),
        Measure(
            kind="thin",
            a=f"{name}.o.stress",
            b=f"{name}.i.stress",
            expected=float(thin),
            direction_deg=90.0 + float(stress_deg),
        ),
    )
    return _with_measures(combined, *measures)


@dataclass(frozen=True, slots=True)
class BarSpec:
    """Horizontal bar for ``open_bowl`` (e-style: one counter + one aperture)."""

    y: float
    thick: float
    inset: float = 0.0


def open_bowl(
    center: PointLike,
    rx: float,
    ry: float,
    *,
    thick: float,
    thin: float,
    aperture: tuple[float, float] | float = 0.42,
    terminal_angle: float | None = None,
    bar: BarSpec | None = None,
    open_side: Side = "right",
    exponent: float = 2.0,
    overshoot: float = 0.0,
    tension: float = 0.55,
    name: str = "bowl",
) -> Drawing:
    """Open superellipse ring with a vertical-chord aperture.

    ``aperture`` may be a y-fraction (0..1, like starters) or an angle pair
    ``(a0, a1)`` in radians; angle pairs are converted to a chord fraction via
    ``sin``. Terminals are end slots ``aperture.0.a`` / ``aperture.0.b``.
    With ``bar``, overlays a crossbar so topology is 1 counter + 1 aperture.
    """
    if float(thick) <= 0 or float(thin) <= 0:
        raise ValueError("thick and thin must be positive")
    c = _as_point(center)
    if isinstance(aperture, tuple):
        a0, a1 = float(aperture[0]), float(aperture[1])
        # Map half-angular width to y-fraction of ry.
        half = 0.5 * abs(a1 - a0)
        y_frac = max(0.06, min(0.94, math.sin(half) if terminal_angle is None else abs(math.sin(float(terminal_angle)))))
    else:
        y_frac = float(aperture)
    if not 0.05 < y_frac < 0.95:
        raise ValueError(f"aperture fraction out of range: {y_frac!r}")

    outer_rx, outer_ry = float(rx), float(ry) + float(overshoot)
    inner_rx = max(outer_rx - float(thick), 1.0)
    inner_ry = max(outer_ry - float(thin), 1.0)
    exp = float(exponent)
    ten = float(tension)
    cx, cy = c.x, c.y

    x_o = _superellipse_x_at_y_frac(outer_rx, y_frac, exp)
    x_i = _superellipse_x_at_y_frac(inner_rx, y_frac, exp)
    y_o = y_frac * outer_ry
    y_i = y_frac * inner_ry
    top_o = (cx + x_o, cy + y_o)
    bot_o = (cx + x_o, cy - y_o)
    top_i = (cx + x_i, cy + y_i)
    bot_i = (cx + x_i, cy - y_i)
    north_o = (cx, cy + outer_ry)
    south_o = (cx, cy - outer_ry)
    north_i = (cx, cy + inner_ry)
    south_i = (cx, cy - inner_ry)

    o1 = superellipse_quarter((cx, cy), outer_rx, outer_ry, 1, exponent=exp)
    o2 = superellipse_quarter((cx, cy), outer_rx, outer_ry, 2, exponent=exp)
    i1 = superellipse_quarter((cx, cy), inner_rx, inner_ry, 1, exponent=exp)
    i2 = superellipse_quarter((cx, cy), inner_rx, inner_ry, 2, exponent=exp)

    stub_top_o = tensioned_arc(
        top_o, _ccw_unit(x_o, y_o), north_o, (-1.0, 0.0), tension=ten
    )
    stub_bot_o = tensioned_arc(
        south_o, (1.0, 0.0), bot_o, _ccw_unit(x_o, -y_o), tension=ten
    )
    stub_top_i = tensioned_arc(
        top_i, _ccw_unit(x_i, y_i), north_i, (-1.0, 0.0), tension=ten
    )
    stub_bot_i = tensioned_arc(
        south_i, (1.0, 0.0), bot_i, _ccw_unit(x_i, -y_i), tension=ten
    )

    # Terminal joins are not G1 (chord across the aperture); mark cusps and
    # declare end slots so ends plugins can finish the stroke.
    w = Writer()
    w.start(top_o).end("aperture.0.a").cusp()
    w.fragment(stub_top_o)
    w.fragment(o1).fragment(o2)
    w.fragment(stub_bot_o)
    w.end("aperture.0.b").cusp()
    w.line(bot_i)
    w.cusp()
    w.fragment(stub_bot_i.reversed())
    w.fragment(i2.reversed()).fragment(i1.reversed())
    w.fragment(stub_top_i.reversed())
    w.cusp()
    w.line(top_o)
    drawing = w.close().build()
    if open_side == "left":
        drawing = drawing.mirrored_x(cx)

    measures: tuple[Measure, ...] = (
        Measure(kind="gap", a="aperture.0.a", b="aperture.0.b"),
        Measure(kind="stem", a="aperture.0.a", expected=float(thick), direction_deg=0.0),
        Measure(kind="thin", a="aperture.0.a", expected=float(thin), direction_deg=90.0),
    )

    if bar is None:
        return _with_measures(drawing, *measures)

    # Bar joins the left inner wall to the lower aperture lip (target §4.3):
    # after pathops unify → exactly 1 counter + 1 aperture (not θ).
    half = float(bar.thick) / 2.0
    bar_y = float(bar.y)
    # Overlap left stem ink so union sticks.
    left_x = cx - outer_rx + max(float(bar.inset), float(thick) * 0.2)
    # Aim the right end at the lower aperture outer terminal (bot_o).
    right_x = float(bot_o[0]) - float(thick) * 0.1
    # Keep the bar below mid so the upper eye closes as the sole counter.
    # Clamp bar_y toward the lower half if the caller passed center.
    bar_y = min(bar_y, cy - float(thin) * 0.1)
    top_y = bar_y + half
    bot_y = bar_y - half
    # Also nudge right end down onto the lower lip y so the seal is real.
    lip_y = float(bot_i[1])
    # Build a wedge-ish bar: left rectangle into a right end near (right_x, lip).
    bar_drawing = (
        Writer()
        .start((left_x, bot_y))
        .corner("bar.b.l")
        .line((left_x, top_y))
        .corner("bar.t.l")
        .line((right_x, top_y))
        .corner("bar.t.r")
        .line((right_x, min(bot_y, lip_y)))
        .corner("bar.b.r")
        .line((left_x, bot_y))
        .close()
        .build()
    )
    return _with_measures(drawing + bar_drawing, *measures)


def bowl_join(
    stem_face_x: float,
    center: PointLike,
    rx: float,
    ry: float,
    *,
    side: Side,
    thick: float,
    thin: float,
    crotch: float,
    exponent: float = 2.0,
    overshoot: float = 0.0,
    tension: float = 0.55,
    name: str = "join",
) -> Drawing:
    """Bowl leaving a vertical stem face, thinned to ``crotch`` at the join."""
    if float(crotch) <= 0 or float(crotch) > float(thick):
        raise ValueError("crotch must be in (0, thick]")
    c = _as_point(center)
    # Open toward the stem; seal with a vertical edge at stem_face_x.
    open_side: Side = "left" if side == "left" else "right"
    body = open_bowl(
        c,
        rx,
        ry,
        thick=thick,
        thin=thin,
        aperture=0.45,
        open_side=open_side,
        exponent=exponent,
        overshoot=overshoot,
        tension=tension,
        name="bowl",
    )
    # Vertical seal strip of width ``crotch`` at the stem face, overlapping the
    # open terminals so pathops unify into one counter without a slit.
    y0 = c.y - float(ry) - float(overshoot) - 1.0
    y1 = c.y + float(ry) + float(overshoot) + 1.0
    if side == "left":
        x0, x1 = float(stem_face_x), float(stem_face_x) + float(crotch)
    else:
        x0, x1 = float(stem_face_x) - float(crotch), float(stem_face_x)
    seal = (
        Writer()
        .start((x0, y0))
        .corner(f"{name}.crotch")
        .line((x0, y1))
        .line((x1, y1))
        .line((x1, y0))
        .line((x0, y0))
        .close()
        .build()
    )
    combined = body + seal
    measures = body.measures + (
        Measure(kind="crotch", a=f"{name}.crotch", expected=float(crotch)),
    )
    return _with_measures(
        Drawing(combined.contours, combined.roles, combined.nodes, combined.slots, ()),
        *measures,
    )


def spine(
    top_terminal: PointLike,
    bottom_terminal: PointLike,
    *,
    thick: float,
    thin: float,
    tension: float,
    axis_deg: float = 0.0,
    name: str = "spine",
) -> Drawing:
    """S-curve stroke; mid thickness ``thick``, terminals taper to ``thin``."""
    if float(thick) <= 0 or float(thin) <= 0:
        raise ValueError("thick and thin must be positive")
    top = _as_point(top_terminal)
    bot = _as_point(bottom_terminal)
    dx, dy = bot.x - top.x, bot.y - top.y
    length = math.hypot(dx, dy)
    if length < 1e-9:
        raise ValueError("spine terminals must differ")
    ux, uy = dx / length, dy / length
    ang = math.radians(float(axis_deg))
    # Left-hand normal, then rotate by axis_deg.
    nx0, ny0 = -uy, ux
    nx = nx0 * math.cos(ang) - ny0 * math.sin(ang)
    ny = nx0 * math.sin(ang) + ny0 * math.cos(ang)

    def offset(p: Point, half: float) -> tuple[Point, Point]:
        return Point(p.x + nx * half, p.y + ny * half), Point(
            p.x - nx * half, p.y - ny * half
        )

    mid = Point(
        top.x + ux * length * 0.5 + nx * float(thick) * 0.2,
        top.y + uy * length * 0.5 + ny * float(thick) * 0.2,
    )
    tl, tr = offset(top, float(thin) / 2.0)
    ml, mr = offset(mid, float(thick) / 2.0)
    bl, br = offset(bot, float(thin) / 2.0)

    left = Fragment(
        tensioned_arc(tl, (ux, uy), ml, (ux, uy), tension=float(tension)).segments
        + tensioned_arc(ml, (ux, uy), bl, (ux, uy), tension=float(tension)).segments
    )
    right = Fragment(
        tensioned_arc(br, (-ux, -uy), mr, (-ux, -uy), tension=float(tension)).segments
        + tensioned_arc(mr, (-ux, -uy), tr, (-ux, -uy), tension=float(tension)).segments
    )
    drawing = (
        Writer()
        .start(tl)
        .end(f"{name}.entry")
        .cusp()
        .fragment(left)
        .end(f"{name}.exit")
        .cusp()
        .line(br)
        .corner(f"{name}.apex")
        .fragment(right)
        .corner(f"{name}.crown")
        .line(tl)
        .close()
        .build()
    )
    measures = (
        Measure(kind="stem", a=f"{name}.entry", expected=float(thin)),
        Measure(kind="stem", a=f"{name}.exit", expected=float(thin)),
    )
    return _with_measures(drawing, *measures)
