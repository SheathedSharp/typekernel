"""Pack glyph outlines to target LSB/RSB (target-architecture §5.3)."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import replace
from typing import Literal

from typekernel.draw.geomutil import map_segment
from typekernel.font.glyph import Glyph
from typekernel.geo.contour import Contour
from typekernel.geo.outline import Outline, bounds
from typekernel.geo.point import Point
from typekernel.system import System

__all__ = ["pack", "translate_outline"]

PackPolicy = Literal["bbox", "slant-mid-x"]


def translate_outline(outline: Outline, dx: float, dy: float = 0.0) -> Outline:
    def move(p: Point) -> Point:
        return Point(p.x + dx, p.y + dy)

    return Outline(
        tuple(
            Contour(tuple(map_segment(s, move) for s in c.segments), closed=c.closed)
            for c in outline.contours
        )
    )


def _italic_silhouette_left(
    outline: Outline, system: System, ys: Sequence[float]
) -> float | None:
    from typekernel.optics.space import silhouette_edge

    xh = float(system.zones.x)
    lefts: list[float] = []
    fracs = tuple(ys) if ys else (0.5,)
    for frac in fracs:
        left = silhouette_edge([outline], xh * float(frac), "left")
        if left is not None:
            lefts.append(float(left))
    if not lefts:
        return None
    return min(lefts)


def pack(
    glyph: Glyph,
    lsb: float,
    rsb: float,
    system: System,
    *,
    policy: PackPolicy | None = None,
    italic_pack_ys: Sequence[float] = (),
) -> Glyph:
    """Shift ink so sidebearing target matches; advance = lsb + bbox_ink + rsb."""
    if not glyph.outline.contours or not any(c.segments for c in glyph.outline.contours):
        return replace(glyph, advance=max(glyph.advance, lsb + rsb))

    chosen: PackPolicy
    if policy is None:
        chosen = "slant-mid-x" if system.is_italic else "bbox"
    else:
        chosen = policy

    min_x, min_y, max_x, max_y = bounds(glyph.outline)
    ink = float(max_x - min_x)
    dx = lsb - float(min_x)

    if chosen == "slant-mid-x" and system.is_italic:
        xh = float(system.zones.x)
        ov = float(system.overshoot.round)
        if min_y >= -ov and max_y <= xh + ov:
            left = _italic_silhouette_left(glyph.outline, system, italic_pack_ys)
            if left is not None:
                dx = lsb - float(left)

    shifted = translate_outline(glyph.outline, dx)
    return replace(glyph, outline=shifted, advance=lsb + ink + rsb)
