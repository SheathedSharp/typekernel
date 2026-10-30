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

from typekernel.draw.drawing import Drawing
from typekernel.geo.contour import Contour, reverse_contour, signed_area
from typekernel.geo.outline import Outline
from typekernel.geo.path_builder import PathBuilder
from typekernel.geo.pens import draw_outline
from typekernel.system import System

__all__ = [
    "Anchor",
    "Component",
    "Glyph",
    "glyph_name_for_char",
    "normalize_winding",
    "notdef_glyph_from_system",
    "space_glyph_from_system",
]

Transform = tuple[float, float, float, float, float, float]
IDENTITY: Transform = (1.0, 0.0, 0.0, 1.0, 0.0, 0.0)


@dataclass(frozen=True, slots=True)
class Anchor:
    """Named attachment point. ``top`` on a base pairs with ``_top`` on a mark.

    Optional ``angle`` (degrees) and ``width`` (stroke) support S3 join
    anchors (``entry`` / ``exit``). UFO / GPOS export uses ``name,x,y`` only.
    """

    name: str
    x: float
    y: float
    angle: float | None = None
    width: float | None = None


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
    """One glyph of a font."""

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
    def from_drawing(
        cls,
        name: str,
        drawing: Drawing,
        *,
        advance: float,
        unicodes: Iterable[int] = (),
        anchors: Iterable[Anchor] = (),
        components: Iterable[Component] = (),
    ) -> Glyph:
        """Bind a :class:`~typekernel.draw.Drawing` outline to a name and metrics."""
        return cls(
            name=name,
            outline=drawing.outline(),
            advance=advance,
            unicodes=tuple(unicodes),
            anchors=tuple(anchors),
            components=tuple(components),
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
    """Orient contours by nesting depth: even depth CCW, odd depth CW."""
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
            if i != j and other.segments and _contains(other, probe.x, probe.y)
        )
        want_positive = (depth % 2 == 0) ^ invert
        if (area > 0) == want_positive:
            out.append(contour)
        else:
            out.append(reverse_contour(contour))
    return Outline(tuple(out))


def notdef_glyph_from_system(system: System) -> Glyph:
    """Hollow-box ``.notdef`` from a :class:`~typekernel.system.System`."""
    xh = float(system.zones.x)
    w = 0.5 * xh
    sb = 0.1 * xh
    x0, y0, x1, y1 = sb, 0.0, sb + w, xh
    inset = 0.08 * xh
    b = PathBuilder()
    b.moveTo(x0, y0)
    b.lineTo(x1, y0)
    b.lineTo(x1, y1)
    b.lineTo(x0, y1)
    b.closePath()
    b.moveTo(x0 + inset, y0 + inset)
    b.lineTo(x0 + inset, y1 - inset)
    b.lineTo(x1 - inset, y1 - inset)
    b.lineTo(x1 - inset, y0 + inset)
    b.closePath()
    return Glyph(".notdef", normalize_winding(b.build()), advance=x1 + sb)


def space_glyph_from_system(system: System, width: float | None = None) -> Glyph:
    """Empty space glyph (U+0020) from a :class:`~typekernel.system.System`."""
    advance = 0.5 * system.zones.x if width is None else width
    return Glyph(
        glyph_name_for_char(" "),
        Outline(()),
        advance=advance,
        unicodes=(0x20,),
    )
