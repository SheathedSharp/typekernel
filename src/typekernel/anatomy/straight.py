"""Straight anatomy parts: stem, crossbar, dot, drop (target-architecture §4.3)."""

from __future__ import annotations

import math
from typing import Literal

from typekernel.draw import Drawing, Measure, Writer, superellipse_quarter, tensioned_arc
from typekernel.geo.point import Point

__all__ = ["crossbar", "dot", "drop", "stem"]

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


def stem(
    x0: float,
    x1: float,
    y0: float,
    y1: float,
    *,
    name: str,
    foot: Literal["slot", "none"] = "slot",
    top: Literal["slot", "none"] = "slot",
) -> Drawing:
    """Closed vertical stem rectangle.

    Width is ``x1 - x0`` (must be positive). Corner tags use ``name`` as the
    part prefix: ``{name}.foot.o`` at ``(x0, y0)``, ``{name}.foot.i`` at
    ``(x1, y0)``, and likewise for ``top``. Declares a ``Measure(kind="stem")``
    between the foot faces.
    """
    width = float(x1) - float(x0)
    if width <= 0:
        raise ValueError(f"stem width must be positive (x1-x0), got {width!r}")
    if float(y1) == float(y0):
        raise ValueError("stem y0 and y1 must differ")
    if not name:
        raise ValueError("stem name must be non-empty")

    def _mark(writer: Writer, tag: str, *, slot: bool) -> Writer:
        return writer.corner(tag) if slot else writer.node(tag)

    w = Writer().start((x0, y0))
    _mark(w, f"{name}.foot.o", slot=(foot == "slot"))
    w.line((x0, y1))
    _mark(w, f"{name}.top.o", slot=(top == "slot"))
    w.line((x1, y1))
    _mark(w, f"{name}.top.i", slot=(top == "slot"))
    w.line((x1, y0))
    _mark(w, f"{name}.foot.i", slot=(foot == "slot"))
    w.line((x0, y0))
    drawing = w.close().build()
    measure = Measure(
        kind="stem",
        a=f"{name}.foot.o",
        b=f"{name}.foot.i",
        expected=width,
        direction_deg=0.0,
    )
    return _with_measures(drawing, measure)


def crossbar(
    x0: float,
    x1: float,
    y: float,
    *,
    thick: float,
    name: str,
    ends: Literal["slot", "none"] = "slot",
) -> Drawing:
    """Horizontal bar spanning ``x0``..``x1``, vertically centered on ``y``.

    Thickness is ``thick``. Corner tags ``{name}.b.l`` / ``.t.l`` / ``.t.r`` /
    ``.b.r`` always exist for measurement. When ``ends="slot"``, left / right
    ends also declare end slots ``{name}.entry`` / ``{name}.exit``.
    """
    if float(thick) <= 0:
        raise ValueError(f"crossbar thick must be positive, got {thick!r}")
    if float(x1) == float(x0):
        raise ValueError("crossbar x0 and x1 must differ")
    if not name:
        raise ValueError("crossbar name must be non-empty")
    half = float(thick) / 2.0
    y0, y1 = float(y) - half, float(y) + half
    left, right = (float(x0), float(x1)) if x1 > x0 else (float(x1), float(x0))

    w = Writer().start((left, y0))
    w.corner(f"{name}.b.l")
    if ends == "slot":
        w.end(f"{name}.entry")
    w.line((left, y1))
    w.corner(f"{name}.t.l")
    w.line((right, y1))
    w.corner(f"{name}.t.r")
    if ends == "slot":
        w.end(f"{name}.exit")
    w.line((right, y0))
    w.corner(f"{name}.b.r")
    w.line((left, y0))
    drawing = w.close().build()
    measure = Measure(
        kind="stem",
        a=f"{name}.b.l",
        b=f"{name}.t.l",
        expected=float(thick),
        direction_deg=90.0,
    )
    return _with_measures(drawing, measure)


def dot(
    center: PointLike,
    diameter: float,
    *,
    shape: Literal["round", "square"] = "round",
    overshoot: float = 0.0,
    name: str = "dot",
) -> Drawing:
    """Dot as a closed ink contour (round superellipse or square)."""
    if float(diameter) <= 0:
        raise ValueError(f"dot diameter must be positive, got {diameter!r}")
    c = _as_point(center)
    r = float(diameter) / 2.0 + float(overshoot)
    if shape == "square":
        drawing = (
            Writer()
            .start((c.x - r, c.y - r))
            .corner(f"{name}.b.l")
            .line((c.x - r, c.y + r))
            .corner(f"{name}.t.l")
            .line((c.x + r, c.y + r))
            .corner(f"{name}.t.r")
            .line((c.x + r, c.y - r))
            .corner(f"{name}.b.r")
            .line((c.x - r, c.y - r))
            .close()
            .build()
        )
        measure = Measure(
            kind="height",
            a=f"{name}.b.l",
            b=f"{name}.t.l",
            expected=2.0 * r,
            direction_deg=90.0,
        )
        return _with_measures(drawing, measure)
    if shape != "round":
        raise ValueError(f"shape must be 'round' or 'square', got {shape!r}")
    frags = [superellipse_quarter(c, r, r, q, exponent=2.0) for q in range(4)]
    w = Writer().start(frags[0].start)
    w.node(f"{name}.stress")
    for frag in frags:
        w.fragment(frag)
    drawing = w.close().build()
    measure = Measure(kind="height", a=f"{name}.stress", expected=2.0 * r)
    return _with_measures(drawing, measure)


def drop(
    top: PointLike,
    bottom: PointLike,
    *,
    width: float,
    tail_curve: float = 0.55,
    name: str = "drop",
) -> Drawing:
    """Teardrop (comma / quote body): single closed contour.

    ``top`` is the wide head tip; ``bottom`` is the tail tip.
    ``width`` is the maximum head width; ``tail_curve`` is tension toward the tip.
    """
    if float(width) <= 0:
        raise ValueError(f"drop width must be positive, got {width!r}")
    if not 0.05 <= float(tail_curve) <= 2.0:
        raise ValueError(f"tail_curve out of range: {tail_curve!r}")
    a = _as_point(top)
    b = _as_point(bottom)
    dx = b.x - a.x
    dy = b.y - a.y
    length = math.hypot(dx, dy)
    if length < 1e-9:
        raise ValueError("drop top and bottom must differ")
    ux, uy = dx / length, dy / length
    nx, ny = -uy, ux
    half = float(width) / 2.0
    head = Point(a.x + ux * length * 0.3, a.y + uy * length * 0.3)
    left = Point(head.x + nx * half, head.y + ny * half)
    right = Point(head.x - nx * half, head.y - ny * half)

    left_down = tensioned_arc(left, (ux, uy), b, (ux, uy), tension=float(tail_curve))
    right_up = tensioned_arc(b, (-ux, -uy), right, (-ux, -uy), tension=float(tail_curve))
    drawing = (
        Writer()
        .start(a)
        .corner(f"{name}.apex")
        .line(left)
        .corner(f"{name}.entry")
        .fragment(left_down)
        .end(f"{name}.exit")
        .fragment(right_up)
        .corner(f"{name}.stress")
        .line(a)
        .close()
        .build()
    )
    measure = Measure(
        kind="stem",
        a=f"{name}.entry",
        b=f"{name}.stress",
        expected=float(width),
    )
    return _with_measures(drawing, measure)
