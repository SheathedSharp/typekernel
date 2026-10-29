"""Terminal anatomy parts: hook, tail, ear, spur (target §4.3 / P3-5)."""

from __future__ import annotations

import math
from typing import Literal

from typekernel.draw import Drawing, Measure, Writer, tensioned_arc
from typekernel.draw import hook as construct_hook
from typekernel.geo.point import Point

__all__ = ["ear", "hook", "spur", "tail"]

PointLike = Point | tuple[float, float]


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


def hook(
    stem_face_x: float,
    y_join: float,
    tip: PointLike,
    *,
    thick: float,
    thin: float,
    depth: float,
    tension: float = 0.55,
    tip_tangent: PointLike | None = None,
    name: str = "hook",
) -> Drawing:
    """Thickened hook from a vertical stem face to ``tip`` (end slot at tip).

    Wraps ``draw.construct.hook`` for the outer path and a parallel thinner
    inner path; closes with a tip end slot and a stem-face join.
    """
    if float(thick) <= 0 or float(thin) <= 0:
        raise ValueError("thick and thin must be positive")
    if float(depth) < 0:
        raise ValueError("depth must be >= 0")
    tip_p = _as_point(tip)
    outer = construct_hook(
        float(stem_face_x),
        float(y_join),
        tip_p,
        depth=float(depth),
        tension=float(tension),
        tip_tangent=tip_tangent,
    )
    # Inner path: inset toward the stem by (thick-thin) roughly along normals.
    # Practical approach: run a second hook with reduced depth and tip pulled in.
    side = 1.0 if tip_p.x >= float(stem_face_x) else -1.0
    inset = float(thick) - float(thin)
    inner_tip = Point(tip_p.x - side * float(thin), tip_p.y)
    inner_face = float(stem_face_x) + side * float(thick)
    # Join height on the inner face sits slightly below/above outer join.
    dy = tip_p.y - float(y_join)
    inner_join_y = float(y_join) + (1.0 if dy > 0 else -1.0) * min(abs(inset) * 0.3, abs(dy) * 0.2)
    inner = construct_hook(
        inner_face,
        inner_join_y,
        inner_tip,
        depth=max(float(depth) - inset * 0.5, float(depth) * 0.5),
        tension=float(tension),
        tip_tangent=tip_tangent,
    )
    # Build closed contour: outer hook, tip end, reverse-ish inner via line joins.
    drawing = (
        Writer()
        .start(outer.start)
        .corner(f"{name}.entry")
        .fragment(outer)
        .end(f"{name}.exit")
        .cusp()
        .line(inner.end)
        .corner(f"{name}.apex")
        .fragment(inner.reversed())
        .corner(f"{name}.crotch")
        .line(outer.start)
        .close()
        .build()
    )
    measures = (
        Measure(kind="stem", a=f"{name}.entry", expected=float(thick)),
        Measure(kind="thin", a=f"{name}.exit", expected=float(thin)),
    )
    return _with_measures(drawing, *measures)


def tail(
    join: PointLike,
    tip: PointLike,
    *,
    thick: float,
    thin: float,
    tension: float = 0.55,
    name: str = "tail",
) -> Drawing:
    """Descending / trailing terminal with end slot at ``tip``."""
    if float(thick) <= 0 or float(thin) <= 0:
        raise ValueError("thick and thin must be positive")
    j = _as_point(join)
    tip_p = _as_point(tip)
    dx, dy = tip_p.x - j.x, tip_p.y - j.y
    length = math.hypot(dx, dy)
    if length < 1e-9:
        raise ValueError("tail join and tip must differ")
    ux, uy = dx / length, dy / length
    nx, ny = -uy, ux
    j_l = Point(j.x + nx * float(thick) / 2.0, j.y + ny * float(thick) / 2.0)
    j_r = Point(j.x - nx * float(thick) / 2.0, j.y - ny * float(thick) / 2.0)
    t_l = Point(tip_p.x + nx * float(thin) / 2.0, tip_p.y + ny * float(thin) / 2.0)
    t_r = Point(tip_p.x - nx * float(thin) / 2.0, tip_p.y - ny * float(thin) / 2.0)
    left = tensioned_arc(j_l, (ux, uy), t_l, (ux, uy), tension=float(tension))
    right = tensioned_arc(t_r, (-ux, -uy), j_r, (-ux, -uy), tension=float(tension))
    drawing = (
        Writer()
        .start(j_l)
        .corner(f"{name}.entry")
        .fragment(left)
        .end(f"{name}.exit")
        .cusp()
        .line(t_r)
        .corner(f"{name}.apex")
        .fragment(right)
        .corner(f"{name}.crotch")
        .line(j_l)
        .close()
        .build()
    )
    return _with_measures(
        drawing,
        Measure(kind="stem", a=f"{name}.entry", expected=float(thick)),
        Measure(kind="thin", a=f"{name}.exit", expected=float(thin)),
    )


def ear(
    join: PointLike,
    tip: PointLike,
    *,
    thick: float,
    tension: float = 0.55,
    name: str = "ear",
) -> Drawing:
    """Small upward / sideways ear terminal (r / g bowl ear)."""
    return tail(
        join,
        tip,
        thick=thick,
        thin=max(float(thick) * 0.55, 1.0),
        tension=tension,
        name=name,
    )


def spur(
    stem_face_x: float,
    y: float,
    *,
    length: float,
    thick: float,
    side: Literal["left", "right"] = "left",
    name: str = "spur",
) -> Drawing:
    """Short spur jutting from a vertical stem face at ``y``."""
    if float(length) <= 0 or float(thick) <= 0:
        raise ValueError("length and thick must be positive")
    side_sign = -1.0 if side == "left" else 1.0
    x0 = float(stem_face_x)
    x1 = x0 + side_sign * float(length)
    half = float(thick) / 2.0
    y0, y1 = float(y) - half, float(y) + half
    left, right = (min(x0, x1), max(x0, x1))
    drawing = (
        Writer()
        .start((left, y0))
        .corner(f"{name}.entry")
        .line((left, y1))
        .line((right, y1))
        .end(f"{name}.exit")
        .line((right, y0))
        .line((left, y0))
        .close()
        .build()
    )
    return _with_measures(
        drawing,
        Measure(kind="stem", a=f"{name}.entry", expected=float(thick), direction_deg=90.0),
    )
