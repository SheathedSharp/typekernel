"""Live renderer: Drawing / Outline → pixels without compiling (target §6.1).

Pipeline (default ``fill_rule="nonzero"``):
  1. Convert cubics to a pathops Path.
  2. ``pathops.simplify`` with nonzero winding (resolve overlaps → outer + holes).
  3. Adaptive-flatten the simplified path to polygons.
  4. Pillow-fill with even-odd (safe once contours no longer overlap).

``fill_rule="evenodd"`` skips the nonzero simplify and fills with even-odd so
tests can contrast the two rules on the same geometry.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Literal

from typekernel.font.glyph import Glyph
from typekernel.geo.contour import Contour
from typekernel.geo.outline import Outline, bounds
from typekernel.geo.point import Point
from typekernel.geo.segment import CubicSegment, LineSegment
from typekernel.geo.stroke import CubicBezier, _flatten_cubic_segment

FillRule = Literal["nonzero", "evenodd"]

__all__ = ["LiveGlyph", "flatten_outline", "render_live", "simplify_outline"]

_BG = (250, 250, 248, 255)
_FG = (32, 32, 36, 255)


@dataclass(frozen=True, slots=True)
class LiveGlyph:
    """One run of ink for live layout (outline + advance)."""

    outline: Outline
    advance: float


def _as_live(item: Outline | LiveGlyph | Glyph) -> LiveGlyph:
    if isinstance(item, LiveGlyph):
        return item
    if isinstance(item, Glyph):
        return LiveGlyph(outline=item.outline, advance=float(item.advance))
    return LiveGlyph(outline=item, advance=0.0)


def simplify_outline(outline: Outline) -> Outline:
    """Return a non-overlapping outline via pathops.simplify (nonzero winding)."""
    import pathops
    from pathops import Path

    from typekernel.geo.boolean import _outline_to_path, _path_to_outline

    path = _outline_to_path(outline, Path)
    simplified = pathops.simplify(path, fix_winding=True)
    return _path_to_outline(simplified)


def flatten_outline(
    outline: Outline,
    *,
    chord_budget: float = 0.5,
) -> list[list[tuple[float, float]]]:
    """Adaptive-flatten closed contours to polylines (preview only).

    Open contours are skipped (live fill only draws closed ink).
    """
    polys: list[list[tuple[float, float]]] = []
    for contour in outline.contours:
        if not contour.closed or not contour.segments:
            continue
        pts: list[tuple[float, float]] = []
        max_err = [0.0]
        for segment in contour.segments:
            if isinstance(segment, LineSegment):
                a = (segment.p0.x, segment.p0.y)
                b = (segment.p1.x, segment.p1.y)
                if not pts or pts[-1] != a:
                    pts.append(a)
                if pts[-1] != b:
                    pts.append(b)
            else:
                assert isinstance(segment, CubicSegment)
                bez = CubicBezier(
                    (segment.p0.x, segment.p0.y),
                    (segment.p1.x, segment.p1.y),
                    (segment.p2.x, segment.p2.y),
                    (segment.p3.x, segment.p3.y),
                )
                _flatten_cubic_segment(bez, chord_budget, pts, max_err)
        if len(pts) >= 3:
            if pts[0] != pts[-1]:
                pts.append(pts[0])
            polys.append(pts)
    return polys


def _layout_bounds(
    items: Sequence[LiveGlyph],
    kerning: Sequence[float] | None,
) -> tuple[float, float, float, float]:
    """Union of shifted glyph bounds across the run."""
    if not items:
        return (0.0, 0.0, 1.0, 1.0)
    min_x = min_y = float("inf")
    max_x = max_y = float("-inf")
    cursor = 0.0
    for i, g in enumerate(items):
        try:
            bx0, by0, bx1, by1 = bounds(g.outline)
        except ValueError:
            cursor += g.advance
            if kerning is not None and i < len(kerning):
                cursor += kerning[i]
            continue
        min_x = min(min_x, cursor + bx0)
        max_x = max(max_x, cursor + bx1)
        min_y = min(min_y, by0)
        max_y = max(max_y, by1)
        cursor += g.advance
        if kerning is not None and i < len(kerning):
            cursor += kerning[i]
    if min_x == float("inf"):
        return (0.0, 0.0, 1.0, 1.0)
    return (min_x, min_y, max_x, max_y)


def _shift_outline(outline: Outline, dx: float) -> Outline:
    if dx == 0.0:
        return outline
    contours: list[Contour] = []
    for contour in outline.contours:
        segs: list[LineSegment | CubicSegment] = []
        for segment in contour.segments:
            pts = tuple(Point(p.x + dx, p.y) for p in segment.points)
            if isinstance(segment, LineSegment):
                segs.append(LineSegment(pts[0], pts[1]))
            else:
                segs.append(CubicSegment(pts[0], pts[1], pts[2], pts[3]))
        contours.append(Contour(tuple(segs), closed=contour.closed))
    return Outline(tuple(contours))


def _xor_fill(
    mask: object,
    polys: list[list[tuple[float, float]]],
    size: tuple[int, int],
) -> object:
    """Even-odd (xor) polygon fill into an ``L`` mask."""
    from PIL import Image, ImageChops, ImageDraw

    assert isinstance(mask, Image.Image)
    for poly in polys:
        if len(poly) < 3:
            continue
        layer = Image.new("L", size, 0)
        ImageDraw.Draw(layer).polygon(poly, fill=255)
        mask = ImageChops.difference(mask, layer)
    return mask


def render_live(
    glyphs: Sequence[Outline | LiveGlyph | Glyph],
    *,
    size: int = 256,
    fill_rule: FillRule = "nonzero",
    kerning: Sequence[float] | None = None,
    background: tuple[int, int, int, int] = _BG,
    foreground: tuple[int, int, int, int] = _FG,
    margin_fraction: float = 0.08,
    supersample: int = 2,
    chord_budget: float | None = None,
) -> object:
    """Rasterise one or more glyphs without compiling.

    Returns a Pillow ``Image.Image`` (RGBA). Multi-glyph runs advance the pen
    by each glyph's ``advance`` plus optional per-gap ``kerning`` values
    (length ``len(glyphs) - 1``).

    Raises:
        ValueError: if ``size`` / ``supersample`` is not positive, or kerning
            length is wrong.
    """
    from PIL import Image

    if size <= 0:
        raise ValueError(f"size must be positive, got {size}")
    if supersample <= 0:
        raise ValueError(f"supersample must be positive, got {supersample}")
    if kerning is not None and len(kerning) not in (0, max(0, len(glyphs) - 1)):
        raise ValueError(
            f"kerning length must be 0 or len(glyphs)-1 "
            f"({max(0, len(glyphs) - 1)}), got {len(kerning)}"
        )

    items = [_as_live(g) for g in glyphs]
    min_x, min_y, max_x, max_y = _layout_bounds(items, kerning)
    width = max(max_x - min_x, 1.0)
    height = max(max_y - min_y, 1.0)

    render_size = size * supersample
    margin = margin_fraction * render_size
    drawable = render_size - 2 * margin
    scale = drawable / max(width, height)
    offset_x = margin + (drawable - width * scale) / 2.0
    offset_y = margin + (drawable - height * scale) / 2.0

    if chord_budget is None:
        chord_budget = max(0.25, 0.5 / max(scale, 1e-9))

    def to_pixel(x: float, y: float) -> tuple[float, float]:
        px = offset_x + (x - min_x) * scale
        py = offset_y + (max_y - y) * scale
        return (px, py)

    image = Image.new("RGBA", (render_size, render_size), background)
    mask: object = Image.new("L", (render_size, render_size), 0)

    cursor = 0.0
    for i, g in enumerate(items):
        outline = _shift_outline(g.outline, cursor)
        if fill_rule == "nonzero":
            try:
                outline = simplify_outline(outline)
            except (ValueError, RuntimeError, TypeError):
                # Empty / degenerate outlines: draw the raw contours instead.
                pass
        polys = flatten_outline(outline, chord_budget=chord_budget)
        pixel_polys = [[to_pixel(x, y) for x, y in poly] for poly in polys]
        mask = _xor_fill(mask, pixel_polys, (render_size, render_size))
        cursor += g.advance
        if kerning is not None and i < len(kerning):
            cursor += kerning[i]

    ink = Image.new("RGBA", (render_size, render_size), foreground)
    assert isinstance(mask, Image.Image)
    image.paste(ink, mask=mask)
    if supersample > 1:
        image = image.resize((size, size), Image.Resampling.LANCZOS)
    return image
