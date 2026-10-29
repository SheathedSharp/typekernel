"""Helpers: Drawing / GlyphDraft → font.Glyph."""

from __future__ import annotations

from collections.abc import Mapping

from fontTools.agl import AGL2UV

from typekernel.draw import Drawing
from typekernel.font.glyph import Anchor, Component, Glyph
from typekernel.geo.outline import bounds
from typekernel.geo.point import Point
from typekernel.project.manifest import ComponentRef

__all__ = [
    "advance_from_drawing",
    "anchors_from_draft",
    "components_from_draft",
    "drawing_to_glyph",
    "unicodes_for_glyph_name",
]


def advance_from_drawing(drawing: Drawing) -> float:
    """BBox width of the drawing outline; ``0.0`` when the outline is empty."""
    outline = drawing.outline()
    if not outline.contours or not any(c.segments for c in outline.contours):
        return 0.0
    min_x, _min_y, max_x, _max_y = bounds(outline)
    return float(max_x - min_x)


def unicodes_for_glyph_name(name: str) -> tuple[int, ...]:
    """Map an AGL / single-character production name to codepoints."""
    cp = AGL2UV.get(name)
    if cp is not None:
        return (int(cp),)
    if len(name) == 1:
        return (ord(name),)
    return ()


def _as_xy(value: object) -> tuple[float, float]:
    if isinstance(value, Point):
        return (float(value.x), float(value.y))
    if isinstance(value, tuple) and len(value) == 2:
        return (float(value[0]), float(value[1]))
    raise TypeError(f"anchor value must be Point or a two-float pair, got {type(value)!r}")


def anchors_from_draft(anchors: Mapping[str, object]) -> tuple[Anchor, ...]:
    return tuple(Anchor(name=k, x=xy[0], y=xy[1]) for k, xy in ((n, _as_xy(v)) for n, v in anchors.items()))


def components_from_draft(refs: tuple[ComponentRef, ...] | list[ComponentRef]) -> tuple[Component, ...]:
    out: list[Component] = []
    for ref in refs:
        out.append(Component(base=ref.base, transform=ref.transform))
    return tuple(out)


def drawing_to_glyph(
    name: str,
    drawing: Drawing,
    *,
    advance: float,
    unicodes: tuple[int, ...] | None = None,
    anchors: tuple[Anchor, ...] = (),
    components: tuple[Component, ...] = (),
) -> Glyph:
    """Wrap a Drawing's contours as a ``font.Glyph``."""
    if unicodes is None:
        unicodes = unicodes_for_glyph_name(name)
    return Glyph.from_drawing(
        name,
        drawing,
        advance=advance,
        unicodes=unicodes,
        anchors=anchors,
        components=components,
    )
