"""Glyph — an outline bound to a name, code points, metrics and attachment data.

:class:`~typekernel.geo.outline.Outline` is deliberately not a glyph. This is
the later binding the geo layer promised: a name, Unicode values, an advance
width, anchors (for marks / diacritics) and components (for reuse by
reference). Outlines inside a :class:`Glyph` use font winding: outer contours
counter-clockwise, counters clockwise (PostScript / UFO convention; ufo2ft
reverses for TrueType).
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field

from fontTools.agl import UV2AGL
from fontTools.pens.pointInsidePen import PointInsidePen

from typekernel.geo.contour import Contour, reverse_contour, signed_area
from typekernel.geo.outline import Outline
from typekernel.geo.path_builder import PathBuilder
from typekernel.geo.pens import draw_outline
from typekernel.parts.compose import ComposedGlyph
from typekernel.parts.context import DesignContext

__all__ = [
    "Anchor",
    "Component",
    "Glyph",
    "glyph_name_for_char",
    "normalize_winding",
    "notdef_glyph",
    "space_glyph",
]

Transform = tuple[float, float, float, float, float, float]
IDENTITY: Transform = (1.0, 0.0, 0.0, 1.0, 0.0, 0.0)


@dataclass(frozen=True, slots=True)
class Anchor:
    """Named attachment point. ``top`` on a base pairs with ``_top`` on a mark."""

    name: str
    x: float
    y: float


@dataclass(frozen=True, slots=True)
class Component:
    """Reference to another glyph, placed with an affine ``transform``.

    ``transform`` is ``(xx, xy, yx, yy, dx, dy)`` as in fontTools pens.
    """

    base: str
    transform: Transform = IDENTITY

    @classmethod
    def offset(cls, base: str, dx: float = 0.0, dy: float = 0.0) -> Component:
        return cls(base, (1.0, 0.0, 0.0, 1.0, dx, dy))


@dataclass(frozen=True, slots=True)
class Glyph:
    """One glyph of a font.

    Attributes:
        name: Glyph name (AGL-style production names are recommended; see
            :func:`glyph_name_for_char`).
        outline: Ink in font winding. May be empty for ``space`` or for
            glyphs built purely from components.
        advance: Advance width in design units.
        unicodes: Code points mapped to this glyph (first is primary).
        anchors: Attachment points for mark positioning.
        components: Other glyphs drawn by reference.
    """

    name: str
    outline: Outline
    advance: float
    unicodes: tuple[int, ...] = ()
    anchors: tuple[Anchor, ...] = ()
    components: tuple[Component, ...] = field(default=())

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("glyph name must be non-empty")
        if len(set(self.unicodes)) != len(self.unicodes):
            raise ValueError(f"glyph {self.name!r} has duplicate unicodes")

    @classmethod
    def from_composed(
        cls,
        name: str,
        composed: ComposedGlyph,
        *,
        unicodes: Iterable[int] = (),
        anchors: Iterable[Anchor] = (),
        components: Iterable[Component] = (),
    ) -> Glyph:
        """Bind a parts-layer :class:`ComposedGlyph` to a name and code points.

        Solids and un-subtracted holes are merged into one outline with font
        winding, so counters stay open after compilation (nonzero fill).
        """
        contours: list[Contour] = []
        for solid in composed.solids:
            contours.extend(normalize_winding(solid).contours)
        for hole in composed.holes:
            contours.extend(normalize_winding(hole, invert=True).contours)
        return cls(
            name=name,
            outline=Outline(tuple(contours)),
            advance=composed.advance,
            unicodes=tuple(unicodes),
            anchors=tuple(anchors),
            components=tuple(components),
        )

    @classmethod
    def for_char(
        cls,
        char: str,
        composed: ComposedGlyph,
        *,
        anchors: Iterable[Anchor] = (),
        components: Iterable[Component] = (),
    ) -> Glyph:
        """Like :meth:`from_composed`, naming and mapping the glyph from ``char``."""
        if len(char) != 1:
            raise ValueError(f"expected one character, got {char!r}")
        return cls.from_composed(
            glyph_name_for_char(char),
            composed,
            unicodes=(ord(char),),
            anchors=anchors,
            components=components,
        )


def glyph_name_for_char(char: str) -> str:
    """AGL production name for ``char`` (``a``, ``comma``), else ``uniXXXX``."""
    if len(char) != 1:
        raise ValueError(f"expected one character, got {char!r}")
    cp = ord(char)
    name = UV2AGL.get(cp)
    if name is not None:
        return str(name)
    return f"uni{cp:04X}" if cp <= 0xFFFF else f"u{cp:05X}"


def _contains(outer: Contour, x: float, y: float) -> bool:
    pen = PointInsidePen(None, (x, y))
    draw_outline(Outline((outer,)), pen)
    return bool(pen.getResult())


def normalize_winding(outline: Outline, *, invert: bool = False) -> Outline:
    """Orient contours by nesting depth: even depth CCW, odd depth CW.

    Nesting is measured only among contours of ``outline``, so separate solids
    passed as separate outlines never cut each other. ``invert`` flips the
    result (used for counters stored apart from their solid).
    """
    contours = outline.contours
    out: list[Contour] = []
    for i, contour in enumerate(contours):
        area = signed_area(contour)
        if not contour.segments or area == 0.0:
            out.append(contour)
            continue
        probe = contour.segments[0].points[0]
        depth = sum(
            1
            for j, other in enumerate(contours)
            if j != i and other.segments and _contains(other, probe.x, probe.y)
        )
        want_ccw = (depth % 2 == 0) != invert
        out.append(contour if (area > 0) == want_ccw else reverse_contour(contour))
    return Outline(tuple(out))


def notdef_glyph(ctx: DesignContext) -> Glyph:
    """Hollow-box ``.notdef`` sized from the family's cap height and stem."""
    stroke = max(ctx.stem * 0.5, 0.04 * ctx.units_per_em)
    sb = 0.05 * ctx.units_per_em
    w = 0.5 * ctx.cap_height + 2.0 * stroke
    x0, x1 = sb, sb + w
    y0, y1 = 0.0, ctx.cap_height

    b = PathBuilder()
    b.moveTo(x0, y0)
    b.lineTo(x1, y0)
    b.lineTo(x1, y1)
    b.lineTo(x0, y1)
    b.closePath()
    b.moveTo(x0 + stroke, y0 + stroke)
    b.lineTo(x0 + stroke, y1 - stroke)
    b.lineTo(x1 - stroke, y1 - stroke)
    b.lineTo(x1 - stroke, y0 + stroke)
    b.closePath()
    return Glyph(".notdef", normalize_winding(b.build()), advance=x1 + sb)


def space_glyph(ctx: DesignContext, width: float | None = None) -> Glyph:
    """Empty ``space`` (U+0020). Default width is half the x-height."""
    advance = 0.5 * ctx.x_height if width is None else width
    return Glyph("space", Outline(()), advance=advance, unicodes=(0x20,))
