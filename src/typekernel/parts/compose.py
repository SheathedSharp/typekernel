"""Compose glyph parts into a metrics-bearing glyph (scene graph → mesh).

Analogous to grouping Three.js meshes: add solid parts and optional counters,
optionally boolean-union the solids so overlaps do not leave notches, subtract
holes with pathops, then pack sidebearings from the shared
:class:`~typekernel.parts.context.DesignContext`.

Boolean / heal policy (library-wide)
------------------------------------
1. **Controls stock Latin (``Controls.build`` / ``build_all``)** — prefer
   single-contour, interpolation-safe constructions. Do **not** auto-heal or
   auto-union on the Controls path; VF masters need stable point counts.
2. **Custom / skeleton / multi-part assemble** — call
   :meth:`GlyphAssembler.union_solids`, :meth:`GlyphAssembler.subtract_holes`,
   and/or :meth:`GlyphAssembler.heal_self_intersections` **explicitly**. Heal
   and boolean ops require ``typekernel[boolean]`` (skia-pathops) and **raise**
   if it is missing — never silently skip.
3. **Post-hoc** — :func:`heal_composed_glyph` is opt-in for agent-drawn outlines
   after boolean work; same raise-on-missing contract when ``heal=True``.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace

from typekernel.geo.boolean import boolean_op, self_union, strip_tiny_contours, union_all
from typekernel.geo.contour import Contour
from typekernel.geo.layout import union_bounds
from typekernel.geo.outline import Outline
from typekernel.geo.point import Point
from typekernel.geo.segment import CubicSegment, LineSegment
from typekernel.geo.stroke import refit_outline_to_cubics
from typekernel.parts.context import DesignContext


@dataclass(frozen=True, slots=True)
class Anchor:
    """Named attachment point. ``top`` on a base pairs with ``_top`` on a mark."""

    name: str
    x: float
    y: float


@dataclass(frozen=True, slots=True)
class ComposedGlyph:
    """A glyph assembled from parts: ink outlines, holes, and advance width.

    ``anchors`` live in the same coordinates as the ink and move with it.
    ``design`` is the parameter record a builder drew from (for example
    :class:`~typekernel.parts.control.NMetrics`), so related forms can derive
    from the control glyph rather than from the bare context.
    """

    solids: tuple[Outline, ...]
    holes: tuple[Outline, ...]
    advance: float
    context: DesignContext
    anchors: tuple[Anchor, ...] = ()
    design: object | None = None

    def translated(self, dx: float, dy: float = 0.0) -> ComposedGlyph:
        """Shift ink and anchors together; advance is unchanged."""
        return replace(
            self,
            solids=tuple(translate_outline(o, dx, dy) for o in self.solids),
            holes=tuple(translate_outline(h, dx, dy) for h in self.holes),
            anchors=tuple(Anchor(a.name, a.x + dx, a.y + dy) for a in self.anchors),
        )

    def anchor(self, name: str) -> Anchor:
        for a in self.anchors:
            if a.name == name:
                return a
        raise KeyError(f"glyph has no anchor {name!r}")


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
    _subtract_holes: bool = False
    _blend: tuple[float, object, float] | None = None
    _ease: tuple[float, float, bool] | None = None
    _heal: bool = False
    _min_contour_area: float | None = None
    _refit: tuple[float, float] | None = None
    _anchors: list[Anchor] = field(default_factory=list)
    _design: object | None = None

    def anchor(self, name: str, x: float, y: float) -> GlyphAssembler:
        """Place an anchor in part coordinates (shifted with the ink on build)."""
        self._anchors = [a for a in self._anchors if a.name != name]
        self._anchors.append(Anchor(name, x, y))
        return self

    def with_design(self, record: object) -> GlyphAssembler:
        """Attach the parameter record this glyph was drawn from."""
        self._design = record
        return self

    def add(self, outline: Outline) -> GlyphAssembler:
        """Add a solid (positive ink) part."""
        self._solids.append(outline)
        return self

    def add_hole(self, outline: Outline) -> GlyphAssembler:
        """Add a counter / hole to subtract at render (or boolean) time."""
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

    def subtract_holes(self) -> GlyphAssembler:
        """Boolean-difference holes from the (possibly unioned) solid.

        Produces a single outline with counters cut out when pathops is
        available. Prefer this over keeping holes as separate contours when
        exporting to UFO/TTF so winding stays unambiguous.
        """
        self._subtract_holes = True
        return self

    def heal_self_intersections(self) -> GlyphAssembler:
        """Self-union solid outlines after union/subtract to dissolve crossings."""
        self._heal = True
        return self

    def strip_tiny(self, min_area: float = 25.0) -> GlyphAssembler:
        """Drop expand/union debris contours smaller than ``min_area``."""
        self._min_contour_area = float(min_area)
        return self

    def refit_cubics(
        self,
        fit_budget: float = 2.5,
        *,
        corner_deg: float = 35.0,
    ) -> GlyphAssembler:
        """Re-fit pathops-flattened solids/holes to cubics before blend."""
        self._refit = (float(fit_budget), float(corner_deg))
        return self

    def blend_joins(
        self,
        radius: float,
        *,
        select: object | None = None,
        tension: float = 1.0,
    ) -> GlyphAssembler:
        """Blend corners after union/subtract with tangent-meeting cubics.

        Replaces fillet-pad patching: crotches, kinks and shoulders become
        one continuous curve (G2 against straight neighbours). Flat stroke
        terminals are kept unless ``select`` says otherwise. See
        :func:`typekernel.geo.joins.blend_corners`.
        """
        self._blend = (radius, select, tension)
        return self

    def ease_curvature(
        self,
        *,
        angle_tol: float = 0.5,
        min_handle: float = 1.0,
        both_ends: bool = True,
    ) -> GlyphAssembler:
        """Optional pass: G2-harmonize straight↔curve joins after blending.

        See :func:`typekernel.geo.joins.ease_curvature`. Safe to chain after
        :meth:`blend_joins`; no-ops where there is no straight/round join.
        ``both_ends`` enables clothoid-style easing on G1–G1 single-cubic quarters.
        """
        self._ease = (angle_tol, min_handle, both_ends)
        return self

    def build(self) -> ComposedGlyph:
        """Pack sidebearings and return an immutable :class:`ComposedGlyph`."""
        solids = list(self._solids)
        if not solids and not self._holes:
            raise ValueError("GlyphAssembler has no parts")
        if self._do_union and solids:
            solids = [union_all(solids)]
        holes = list(self._holes)
        if self._subtract_holes and holes:
            if not solids:
                raise ValueError("subtract_holes requires at least one solid")
            body = solids[0] if len(solids) == 1 else union_all(solids)
            for hole in holes:
                body = boolean_op(body, hole, "difference")
            solids = [body]
            holes = []
        if self._heal:
            # Explicit heal must not silently no-op when pathops is missing.
            solids = [self_union(solid) for solid in solids]
        if self._min_contour_area is not None:
            solids = [
                strip_tiny_contours(s, min_area=self._min_contour_area) for s in solids
            ]
            holes = [
                strip_tiny_contours(h, min_area=self._min_contour_area) for h in holes
            ]
            holes = [h for h in holes if h.contours]
        if self._refit is not None:
            budget, corner = self._refit
            solids = [
                refit_outline_to_cubics(s, fit_budget=budget, corner_deg=corner)
                for s in solids
            ]
            holes = [
                refit_outline_to_cubics(h, fit_budget=budget, corner_deg=corner)
                for h in holes
            ]
        if self._blend is not None:
            from typekernel.geo.joins import blend_corners, default_selector

            radius, select, tension = self._blend
            sel = default_selector if select is None else select
            solids = [
                blend_corners(o, radius, select=sel, tension=tension)  # type: ignore[arg-type]
                for o in solids
            ]
        if self._ease is not None:
            from typekernel.geo.joins import ease_curvature as _ease_curvature

            angle_tol, min_handle, both_ends = self._ease
            solids = [
                _ease_curvature(
                    o, angle_tol=angle_tol, min_handle=min_handle, both_ends=both_ends
                )
                for o in solids
            ]
            holes = [
                _ease_curvature(
                    h, angle_tol=angle_tol, min_handle=min_handle, both_ends=both_ends
                )
                for h in holes
            ]
        ink = solids + holes
        box = union_bounds(ink)
        ink_w = box[2] - box[0]
        sb = max(
            0.025 * self.context.units_per_em,
            self.context.sidebearing_ratio * self.context.x_height,
        )
        # Keep sidebearings nearly uniform so letter-to-letter gaps read even.
        # Only a tiny width adjust — coding rhythm prefers tabular-ish air.
        scale = self.context.x_height / max(ink_w, 1.0)
        scale = max(0.97, min(1.03, scale))
        sb *= scale
        dx = sb - box[0]
        advance = sb + ink_w + sb
        raw = ComposedGlyph(
            tuple(solids),
            tuple(holes),
            advance,
            self.context,
            anchors=tuple(self._anchors),
            design=self._design,
        )
        return raw.translated(dx)


def translate_outline(outline: Outline, dx: float, dy: float = 0.0) -> Outline:
    """Return a copy of ``outline`` shifted by ``(dx, dy)``.

    Prefer :func:`typekernel.parts.transforms.translate` for new agent code;
    this alias stays for older recipes.
    """

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


def try_union(outlines: list[Outline]) -> Outline:
    """Union outlines via pathops (raises if the boolean extra is missing).

    Same contract as :func:`~typekernel.geo.boolean.union_all` — agents must
    install ``typekernel[boolean]`` rather than relying on a silent fallback.
    """
    return union_all(outlines)


def try_difference(a: Outline, b: Outline) -> Outline:
    """Difference ``a − b`` via pathops (raises if the boolean extra is missing)."""
    return boolean_op(a, b, "difference")


def try_intersection(a: Outline, b: Outline) -> Outline:
    """Intersection via pathops (raises if the boolean extra is missing)."""
    return boolean_op(a, b, "intersection")


def heal_composed_glyph(
    glyph: ComposedGlyph,
    *,
    heal: bool = True,
    min_contour_area: float | None = 25.0,
    refit_budget: float | None = 2.5,
    corner_deg: float = 35.0,
) -> ComposedGlyph:
    """Post-process an existing glyph: self-union, strip debris, refit cubics.

    Agents drawing custom outlines (or boolean-composited parts) can call this
    without rebuilding through :class:`GlyphAssembler`. ``heal`` dissolves
    self-crossings via pathops self-union; ``min_contour_area`` drops speck
    contours; ``refit_budget`` re-fits pathops LINE debris to cubics (``None``
    skips refit). Requires ``typekernel[boolean]`` when ``heal`` is True.
    """
    solids = list(glyph.solids)
    holes = list(glyph.holes)
    if heal:
        # Explicit heal=True requires pathops; do not pretend crossings dissolved.
        solids = [self_union(solid) for solid in solids]
    if min_contour_area is not None:
        solids = [
            strip_tiny_contours(s, min_area=float(min_contour_area)) for s in solids
        ]
        holes = [
            strip_tiny_contours(h, min_area=float(min_contour_area)) for h in holes
        ]
        holes = [h for h in holes if h.contours]
    if refit_budget is not None:
        budget = float(refit_budget)
        solids = [
            refit_outline_to_cubics(s, fit_budget=budget, corner_deg=corner_deg)
            for s in solids
        ]
        holes = [
            refit_outline_to_cubics(h, fit_budget=budget, corner_deg=corner_deg)
            for h in holes
        ]
    return replace(
        glyph,
        solids=tuple(solids),
        holes=tuple(holes),
    )
