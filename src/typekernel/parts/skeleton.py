"""Skeleton-to-outline letter tracing (shape-agnostic).

Compose named centerline strokes, expand with a contrast pen, then optionally
union / blend / ease into a :class:`~typekernel.parts.compose.ComposedGlyph`.

This is construction infrastructure — not a glyph-/face-specific beauty pass
and not a weight axis. Synthetic stroke graphs first; Latin recipes can call
:func:`trace_letter` later without hardcoding family names here.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any, Literal

from typekernel.geo.contour import signed_area
from typekernel.geo.outline import Outline
from typekernel.geo.stroke import CapStyle, Centerline, JoinStyle, expand
from typekernel.parts.compose import ComposedGlyph, GlyphAssembler
from typekernel.parts.context import DesignContext
from typekernel.parts.pen import pen_from_context

TerminalKind = Literal["none", "shear", "flat", "ball", "hook"]

__all__ = [
    "EndTreatment",
    "Skeleton",
    "Stroke",
    "TerminalKind",
    "trace_letter",
]


@dataclass(frozen=True, slots=True)
class EndTreatment:
    """Optional terminal applied at one end of an open stroke after expand."""

    kind: TerminalKind = "none"
    angle_deg: float = 0.0
    size: float | None = None
    """Ball / hook radius; defaults to half stem when omitted."""
    width: float | None = None
    """Hook stroke width; defaults to stem when omitted."""
    sweep_deg: float = 180.0
    start_deg: float = 180.0
    keep: Literal["positive", "negative"] = "positive"
    """Half-plane kept by :func:`~typekernel.parts.terminals.flat_end`."""


def _as_end(value: EndTreatment | TerminalKind | None) -> EndTreatment:
    if value is None or value == "none":
        return EndTreatment()
    if isinstance(value, EndTreatment):
        return value
    return EndTreatment(kind=value)


@dataclass(frozen=True, slots=True)
class Stroke:
    """One named centerline in a letter skeleton.

    Attributes:
        name: Unique id within the skeleton (``\"stem\"``, ``\"bar\"``, …).
        points: Polyline vertices in design units.
        closed: Closed centerline → annular ribbon (outer + hole).
        thickness / contrast / angle_deg: Pen overrides; ``None`` uses context.
        join / cap: Per-stroke styles; ``None`` inherits :func:`trace_letter` defaults.
        start / end: Optional terminal treatments (open strokes only).
    """

    name: str
    points: tuple[tuple[float, float], ...]
    closed: bool = False
    thickness: float | None = None
    contrast: float | None = None
    angle_deg: float = 0.0
    join: JoinStyle | None = None
    cap: CapStyle | None = None
    start: EndTreatment | TerminalKind | None = None
    end: EndTreatment | TerminalKind | None = None

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("stroke name must be non-empty")
        if len(self.points) < 2:
            raise ValueError(f"stroke {self.name!r} needs at least two points")
        if self.closed and (self.start is not None or self.end is not None):
            # Closed ribbons have no free ends.
            object.__setattr__(self, "start", None)
            object.__setattr__(self, "end", None)

    @classmethod
    def from_points(
        cls,
        name: str,
        points: Sequence[tuple[float, float]],
        *,
        closed: bool = False,
        thickness: float | None = None,
        contrast: float | None = None,
        angle_deg: float = 0.0,
        join: JoinStyle | None = None,
        cap: CapStyle | None = None,
        start: EndTreatment | TerminalKind | None = None,
        end: EndTreatment | TerminalKind | None = None,
    ) -> Stroke:
        return cls(
            name=name,
            points=tuple((float(x), float(y)) for x, y in points),
            closed=closed,
            thickness=thickness,
            contrast=contrast,
            angle_deg=angle_deg,
            join=join,
            cap=cap,
            start=start,
            end=end,
        )


@dataclass(frozen=True, slots=True)
class Skeleton:
    """Shape-agnostic stroke graph: ordered named centerlines.

    Junctions are implicit — overlapping expanded strokes are boolean-unioned
    by :func:`trace_letter` when ``union=True``. No face-specific topology.
    """

    strokes: tuple[Stroke, ...]

    def __post_init__(self) -> None:
        if not self.strokes:
            raise ValueError("skeleton needs at least one stroke")
        names = [s.name for s in self.strokes]
        if len(names) != len(set(names)):
            raise ValueError(f"duplicate stroke names: {names!r}")

    @classmethod
    def of(cls, *strokes: Stroke) -> Skeleton:
        return cls(strokes)

    @classmethod
    def from_polylines(
        cls,
        named: Mapping[str, Sequence[tuple[float, float]]],
        *,
        closed: Mapping[str, bool] | Sequence[str] | None = None,
        thickness: float | None = None,
        contrast: float | None = None,
        angle_deg: float = 0.0,
        join: JoinStyle | None = None,
        cap: CapStyle | None = None,
    ) -> Skeleton:
        """Build from ``{name: points, …}``; ``closed`` marks ring strokes."""
        if not named:
            raise ValueError("from_polylines needs at least one polyline")
        closed_set: set[str]
        closed_map: Mapping[str, bool]
        if closed is None:
            closed_set, closed_map = set(), {}
        elif isinstance(closed, Mapping):
            closed_set, closed_map = set(), closed
        else:
            closed_set, closed_map = set(closed), {}
        strokes = [
            Stroke.from_points(
                name,
                pts,
                closed=closed_map.get(name, name in closed_set),
                thickness=thickness,
                contrast=contrast,
                angle_deg=angle_deg,
                join=join,
                cap=cap,
            )
            for name, pts in named.items()
        ]
        return cls(tuple(strokes))

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> Skeleton:
        """Parse a plan-style ``skeleton_dict``.

        Each value is either a point sequence or a dict with keys::

            points, closed, thickness, contrast, angle_deg, join, cap, start, end
        """
        if not data:
            raise ValueError("skeleton mapping is empty")
        strokes: list[Stroke] = []
        for name, raw in data.items():
            if isinstance(raw, Mapping):
                pts = raw.get("points")
                if pts is None:
                    raise ValueError(f"stroke {name!r} dict needs 'points'")
                strokes.append(
                    Stroke.from_points(
                        str(name),
                        pts,
                        closed=bool(raw.get("closed", False)),
                        thickness=raw.get("thickness"),
                        contrast=raw.get("contrast"),
                        angle_deg=float(raw.get("angle_deg", 0.0)),
                        join=raw.get("join"),
                        cap=raw.get("cap"),
                        start=raw.get("start"),
                        end=raw.get("end"),
                    )
                )
            else:
                strokes.append(Stroke.from_points(str(name), raw))
        return cls(tuple(strokes))


def _apply_terminal(
    outline: Outline,
    at: tuple[float, float],
    treatment: EndTreatment,
    ctx: DesignContext,
) -> Outline:
    if treatment.kind == "none":
        return outline
    size = treatment.size if treatment.size is not None else ctx.stem * 0.55
    if treatment.kind == "shear":
        from typekernel.parts.terminals import shear_end

        return shear_end(outline, at, treatment.angle_deg)
    if treatment.kind == "flat":
        from typekernel.parts.terminals import flat_end

        return flat_end(
            outline,
            at,
            angle_deg=treatment.angle_deg,
            keep=treatment.keep,
        )
    if treatment.kind == "ball":
        from typekernel.parts.terminals import ball_end

        return ball_end(outline, at, radius=size, ctx=ctx)
    if treatment.kind == "hook":
        from typekernel.parts.terminals import hook_end

        width = treatment.width if treatment.width is not None else ctx.stem
        return hook_end(
            outline,
            at,
            radius=max(size, width + 1.0),
            width=width,
            sweep_deg=treatment.sweep_deg,
            start_deg=treatment.start_deg,
            ctx=ctx,
        )
    raise ValueError(f"unknown terminal kind: {treatment.kind!r}")



def _ensure_ccw_solid(outline: Outline) -> Outline:
    """Flip solid contours to CCW so pathops unions succeed with closed ribbons."""
    from typekernel.geo.contour import reverse_contour, signed_area

    contours = []
    for c in outline.contours:
        if signed_area(c) < 0:
            contours.append(reverse_contour(c))
        else:
            contours.append(c)
    return Outline(tuple(contours)) if contours != list(outline.contours) else outline


def _split_closed_ribbon(outline: Outline) -> tuple[list[Outline], list[Outline]]:
    """Split an annular expand into solid outers and hole inners by signed area."""
    solids: list[Outline] = []
    holes: list[Outline] = []
    for contour in outline.contours:
        piece = Outline((contour,))
        if signed_area(contour) < 0:
            holes.append(piece)
        else:
            solids.append(piece)
    if not solids and holes:
        # Degenerate winding — treat all as solids.
        return holes, []
    return solids, holes


def _expand_stroke(
    stroke: Stroke,
    ctx: DesignContext,
    *,
    default_join: JoinStyle,
    default_cap: CapStyle,
    miter_limit: float,
) -> tuple[list[Outline], list[Outline]]:
    pen = pen_from_context(
        ctx,
        thickness=stroke.thickness,
        contrast=stroke.contrast,
        angle_deg=stroke.angle_deg,
    )
    cl = Centerline.from_points(stroke.points, closed=stroke.closed)
    join = stroke.join if stroke.join is not None else default_join
    cap = stroke.cap if stroke.cap is not None else default_cap
    outline = expand(cl, pen, join=join, cap=cap, miter_limit=miter_limit)
    if stroke.closed:
        return _split_closed_ribbon(outline)

    start = _as_end(stroke.start)
    end = _as_end(stroke.end)
    if start.kind != "none":
        outline = _apply_terminal(outline, stroke.points[0], start, ctx)
    if end.kind != "none":
        outline = _apply_terminal(outline, stroke.points[-1], end, ctx)
    return [outline], []


def trace_letter(
    skeleton: Skeleton | Mapping[str, Any],
    ctx: DesignContext,
    *,
    union: bool = True,
    blend: bool | float = True,
    ease: bool = False,
    join: JoinStyle = "round",
    cap: CapStyle = "round",
    miter_limit: float = 4.0,
    subtract_holes: bool = True,
) -> ComposedGlyph:
    """Expand a stroke-graph skeleton into a metrics-bearing glyph.

    Parameters:
        skeleton: :class:`Skeleton` or plan-style ``skeleton_dict`` mapping.
        ctx: Shared :class:`~typekernel.parts.context.DesignContext`.
        union: Boolean-union expanded strokes (needs pathops).
        blend: ``True`` → blend with ``ctx.join_radius``; ``float`` → that
            radius; ``False`` → skip corner blending.
        ease: Run :meth:`GlyphAssembler.ease_curvature` after blend.
        join / cap: Default pen join/cap for strokes that omit their own.
        miter_limit: Forwarded to :func:`~typekernel.geo.stroke.expand`.
        subtract_holes: Boolean-subtract closed-stroke holes from the body.

    Returns:
        A :class:`~typekernel.parts.compose.ComposedGlyph` with packed
        sidebearings — same packaging path as hand-built part recipes.
    """
    skel = skeleton if isinstance(skeleton, Skeleton) else Skeleton.from_mapping(skeleton)
    asm = GlyphAssembler(ctx)
    any_holes = False
    for stroke in skel.strokes:
        solids, holes = _expand_stroke(
            stroke,
            ctx,
            default_join=join,
            default_cap=cap,
            miter_limit=miter_limit,
        )
        for solid in solids:
            asm.add(_ensure_ccw_solid(solid))
        for hole in holes:
            asm.add_hole(hole)
            any_holes = True
    if union:
        asm.union_solids()
    if subtract_holes and any_holes:
        asm.subtract_holes()
    if blend is not False:
        radius = float(ctx.join_radius if blend is True else blend)
        if radius > 0:
            asm.blend_joins(radius)
    if ease:
        asm.ease_curvature()
    try:
        return asm.build()
    except Exception as exc:
        # Disjoint round-cap strokes can make pathops union fail; fall back to
        # separate solids so skeleton recipes stay usable.
        name = type(exc).__name__
        if not union or "PathOps" not in name:
            raise
        asm_fb = GlyphAssembler(ctx)
        for stroke in skel.strokes:
            solids, holes = _expand_stroke(
                stroke,
                ctx,
                default_join=join,
                default_cap=cap,
                miter_limit=miter_limit,
            )
            for solid in solids:
                asm_fb.add(_ensure_ccw_solid(solid))
            for hole in holes:
                asm_fb.add_hole(hole)
        if subtract_holes and any_holes:
            # holes without union: keep as separate hole contours
            pass
        if blend is not False:
            radius = float(ctx.join_radius if blend is True else blend)
            if radius > 0:
                asm_fb.blend_joins(radius)
        if ease:
            asm_fb.ease_curvature()
        return asm_fb.build()
