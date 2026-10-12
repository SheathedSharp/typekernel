"""Compose glyph parts into a metrics-bearing glyph (scene graph → mesh).

Analogous to grouping Three.js meshes: add solid parts and optional counters,
optionally boolean-union the solids so overlaps do not leave notches, then
pack sidebearings from the shared :class:`~typekernel.parts.context.DesignContext`.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from typekernel.geo.boolean import union_all
from typekernel.geo.contour import Contour
from typekernel.geo.layout import union_bounds
from typekernel.geo.outline import Outline
from typekernel.geo.point import Point
from typekernel.geo.segment import CubicSegment, LineSegment
from typekernel.parts.context import DesignContext


@dataclass(frozen=True, slots=True)
class ComposedGlyph:
    """A glyph assembled from parts: ink outlines, holes, and advance width."""

    solids: tuple[Outline, ...]
    holes: tuple[Outline, ...]
    advance: float
    context: DesignContext


@dataclass
class GlyphAssembler:
    """Accumulate parts under one :class:`DesignContext`, then bake a glyph.

    Example::

        ctx = DesignContext.geometric_sans()
        g = (
            GlyphAssembler(ctx)
            .add(vertical_stem(ctx, 0, 0, ctx.x_height))
            .add(horizontal_bar(ctx, 0, 300, ctx.x_height - ctx.thin))
            .union_solids()
            .build()
        )
    """

    context: DesignContext
    _solids: list[Outline] = field(default_factory=list)
    _holes: list[Outline] = field(default_factory=list)
    _do_union: bool = False

    def add(self, outline: Outline) -> GlyphAssembler:
        """Add a solid (positive ink) part."""
        self._solids.append(outline)
        return self

    def add_hole(self, outline: Outline) -> GlyphAssembler:
        """Add a counter / hole to subtract at render time."""
        self._holes.append(outline)
        return self

    def union_solids(self) -> GlyphAssembler:
        """Request a boolean union of all solid parts when :meth:`build` runs.

        Requires the optional ``typekernel[boolean]`` extra (skia-pathops).
        Without it, overlapping parts stay as separate contours and may show
        notches where they meet — prefer designing clean fillets, or install
        the extra.
        """
        self._do_union = True
        return self

    def build(self) -> ComposedGlyph:
        """Pack sidebearings and return an immutable :class:`ComposedGlyph`."""
        solids = list(self._solids)
        if not solids and not self._holes:
            raise ValueError("GlyphAssembler has no parts")
        if self._do_union and solids:
            solids = [union_all(solids)]
        holes = list(self._holes)
        ink = solids + holes
        box = union_bounds(ink)
        ink_w = box[2] - box[0]
        sb = max(
            0.04 * self.context.units_per_em,
            self.context.sidebearing_ratio * self.context.x_height,
        )
        # Narrow glyphs get a little more air (same spirit as optics heuristic).
        scale = self.context.x_height / max(ink_w, 1.0)
        scale = max(0.55, min(1.45, scale))
        sb *= scale
        dx = sb - box[0]
        solids_t = tuple(translate_outline(o, dx) for o in solids)
        holes_t = tuple(translate_outline(h, dx) for h in holes)
        advance = sb + ink_w + sb
        return ComposedGlyph(solids_t, holes_t, advance, self.context)


def translate_outline(outline: Outline, dx: float, dy: float = 0.0) -> Outline:
    """Return a copy of ``outline`` shifted by ``(dx, dy)``."""

    def tp(p: Point) -> Point:
        return Point(p.x + dx, p.y + dy)

    contours: list[Contour] = []
    for c in outline.contours:
        segs: list[LineSegment | CubicSegment] = []
        for s in c.segments:
            pts = [tp(p) for p in s.points]
            if isinstance(s, LineSegment):
                segs.append(LineSegment(pts[0], pts[1]))
            else:
                segs.append(CubicSegment(*pts))
        contours.append(Contour(tuple(segs), closed=c.closed))
    return Outline(tuple(contours))
