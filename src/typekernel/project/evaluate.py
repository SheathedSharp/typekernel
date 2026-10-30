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


def _as_anchor_fields(value: object) -> tuple[float, float, float | None, float | None]:
    """Parse draft anchor value → ``(x, y, angle, width)``.

    Accepted forms: ``Point``, ``(x, y)``, ``(x, y, angle)``,
    ``(x, y, angle, width)``, or an object with ``.x/.y`` and optional
    ``.angle`` / ``.width``.
    """
    if isinstance(value, Point):
        return (float(value.x), float(value.y), None, None)
    if isinstance(value, tuple):
        if len(value) == 2:
            return (float(value[0]), float(value[1]), None, None)
        if len(value) == 3:
            return (float(value[0]), float(value[1]), float(value[2]), None)
        if len(value) == 4:
            return (
                float(value[0]),
                float(value[1]),
                float(value[2]),
                float(value[3]),
            )
    # Duck-typed JoinAnchor / similar.
    x = getattr(value, "x", None)
    y = getattr(value, "y", None)
    if x is not None and y is not None:
        ang = getattr(value, "angle", None)
        wid = getattr(value, "width", None)
        return (
            float(x),
            float(y),
            float(ang) if ang is not None else None,
            float(wid) if wid is not None else None,
        )
    raise TypeError(
        "anchor value must be Point, (x, y[, angle[, width]]), "
        f"or an object with x/y, got {type(value)!r}"
    )


def anchors_from_draft(anchors: Mapping[str, object]) -> tuple[Anchor, ...]:
    out: list[Anchor] = []
    for name, value in anchors.items():
        x, y, angle, width = _as_anchor_fields(value)
        out.append(Anchor(name=name, x=x, y=y, angle=angle, width=width))
    return tuple(out)


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
