"""Parameterised letter recipes on continuous curves (not polyline beads).

Arches / bowls are cubic or superellipse outlines from
:mod:`typekernel.parts.primitives`, then unioned and blend-joined. Stem-only
glyphs may still use a single stroke expand. Context-driven — no face-specific
beauty hacks.

Construction path (arched letters)::

    vertical_stem + arch|u_bowl|bowl  →  GlyphAssembler.union + blend_joins
    → optional shallow flat/shear terminals
"""

from __future__ import annotations

from collections.abc import Callable, Mapping

from typekernel.geo.path_builder import PathBuilder
from typekernel.geo.path_helpers import KAPPA
from typekernel.parts.compose import ComposedGlyph, GlyphAssembler
from typekernel.parts.context import DesignContext
from typekernel.parts.primitives import (
    bowl,
    tittle,
    u_bowl,
    vertical_stem,
)
from typekernel.parts.skeleton import Skeleton, Stroke
from typekernel.parts.terminals import shear_end

__all__ = [
    "SKEL_BUILDERS",
    "build_skel_letter",
    "build_skel_word",
    "skel_c",
    "skel_h",
    "skel_i",
    "skel_l",
    "skel_n",
    "skel_o",
    "skel_u",
    "skeleton_c",
    "skeleton_h",
    "skeleton_i",
    "skeleton_l",
    "skeleton_n",
    "skeleton_o",
    "skeleton_u",
]


def _counter_width(ctx: DesignContext) -> float:
    """Inner counter width between stem **inner faces** (matches ``arch``)."""
    return ctx.x_height * (0.46 + 0.12 * ctx.aperture)


def _superellipse_n(ctx: DesignContext) -> float:
    """Squarer bowls when ``roundness`` is low (coding); rounder when soft."""
    # roundness 0 → n≈2.6 (slightly squircle); roundness 1 → n≈2.0 (ellipse)
    return 2.0 + 0.7 * (1.0 - max(0.0, min(1.0, ctx.roundness)))


def _blend_radius(ctx: DesignContext) -> float:
    """Shoulder-to-stem inner corner blend — optical, not a deep notch."""
    return max(ctx.join_radius * 1.15, ctx.stem * 0.22)



def _continuous_arch(
    ctx: DesignContext,
    x_left: float,
    x_right: float,
    y_join: float,
    y_top: float,
    *,
    thickness: float | None = None,
) -> object:
    """n/h shoulder as a closed trough with cubic crown (no tall vertical risers).

    ``x_left`` / ``x_right`` are stem **inner** faces. Outer/inner crowns are
    two cubics each with horizontal tangent at the peak — continuous curves,
    not polyline beads.
    """
    from typekernel.geo.outline import Outline

    th = ctx.stem if thickness is None else thickness
    mid = (x_left + x_right) / 2.0
    span = x_right - x_left
    rise = min(span * 0.08, max(2.0, (y_top - y_join) * 0.22))
    k = KAPPA * (0.95 + 0.25 * ctx.roundness)  # softer when roundness high
    b = PathBuilder()
    b.moveTo(x_left, y_join)
    b.lineTo(x_left, y_join + rise)
    b.curveTo(
        x_left,
        y_join + rise + k * (y_top - y_join - rise),
        mid - k * (mid - x_left),
        y_top,
        mid,
        y_top,
    )
    b.curveTo(
        mid + k * (x_right - mid),
        y_top,
        x_right,
        y_join + rise + k * (y_top - y_join - rise),
        x_right,
        y_join + rise,
    )
    b.lineTo(x_right, y_join)
    b.lineTo(x_right - th, y_join)
    inner_top = y_top - th
    inner_rise = rise * 0.75
    b.lineTo(x_right - th, y_join + inner_rise)
    b.curveTo(
        x_right - th,
        y_join + inner_rise + k * (inner_top - y_join - inner_rise),
        mid + k * (x_right - th - mid),
        inner_top,
        mid,
        inner_top,
    )
    b.curveTo(
        mid - k * (mid - (x_left + th)),
        inner_top,
        x_left + th,
        y_join + inner_rise + k * (inner_top - y_join - inner_rise),
        x_left + th,
        y_join + inner_rise,
    )
    b.lineTo(x_left + th, y_join)
    b.closePath()
    out: Outline = b.build()
    return out


def _shallow_shear_deg(ctx: DesignContext) -> float:
    """Controlled terminal shear (degrees); stays subtle across apertures."""
    return 4.0 + 4.0 * ctx.aperture  # ≈4°…8°, not the old 10°…18° “bone” cuts


def _assemble(
    ctx: DesignContext,
    *parts: object,
    holes: tuple[object, ...] = (),
    blend: bool | float = True,
    subtract_holes: bool = False,
) -> ComposedGlyph:
    from typekernel.geo.outline import Outline

    asm = GlyphAssembler(ctx)
    for p in parts:
        assert isinstance(p, Outline)
        asm.add(p)
    for h in holes:
        assert isinstance(h, Outline)
        asm.add_hole(h)
    if len(parts) > 1:
        asm.union_solids()
    if subtract_holes and holes:
        asm.subtract_holes()
    if blend is not False:
        radius = float(_blend_radius(ctx) if blend is True else blend)
        if radius > 0:
            asm.blend_joins(radius)
    return asm.build()


# --- stroke-graph sketches (documentation / tests; not bead-traced) ----------


def skeleton_l(ctx: DesignContext) -> Skeleton:
    """Single vertical centerline (stem-only; safe to pen-expand)."""
    return Skeleton.of(
        Stroke.from_points("stem", [(0.0, 0.0), (0.0, ctx.ascender)])
    )


def skeleton_i(ctx: DesignContext) -> Skeleton:
    """Stem + tittle markers (tittle is a filled disk recipe, not a ring)."""
    top = ctx.x_height
    cy = top + ctx.stem * 0.85
    return Skeleton.of(
        Stroke.from_points("stem", [(0.0, 0.0), (0.0, top)]),
        Stroke.from_points("tittle", [(0.0, cy), (0.0, cy + 1.0)]),
    )


def skeleton_n(ctx: DesignContext) -> Skeleton:
    """Logical stroke graph for ``n`` (left / arch / right) — metrics only."""
    w = _counter_width(ctx)
    top = ctx.x_height + ctx.overshoot
    # Arch represented as two endpoints + crown (not a dense polyline to expand).
    return Skeleton.of(
        Stroke.from_points("left", [(0.0, 0.0), (0.0, top)]),
        Stroke.from_points("arch", [(0.0, top * 0.55), (w / 2.0, top), (w, top * 0.55)]),
        Stroke.from_points("right", [(w, top * 0.55), (w, 0.0)]),
    )


def skeleton_h(ctx: DesignContext) -> Skeleton:
    w = _counter_width(ctx)
    top = ctx.x_height + ctx.overshoot
    return Skeleton.of(
        Stroke.from_points("left", [(0.0, 0.0), (0.0, ctx.ascender)]),
        Stroke.from_points("arch", [(0.0, top * 0.55), (w / 2.0, top), (w, top * 0.55)]),
        Stroke.from_points("right", [(w, top * 0.55), (w, 0.0)]),
    )


def skeleton_o(ctx: DesignContext) -> Skeleton:
    """Ring marker (actual outline is superellipse bowl)."""
    ry = ctx.x_height / 2.0 + ctx.overshoot
    rx = ry * (0.88 + 0.10 * ctx.aperture)
    return Skeleton.of(
        Stroke.from_points(
            "ring",
            [(rx, 0.0), (2 * rx, ry), (rx, 2 * ry), (0.0, ry)],
            closed=True,
        )
    )


def skeleton_c(ctx: DesignContext) -> Skeleton:
    ry = ctx.x_height / 2.0 + ctx.overshoot
    rx = ry * (0.88 + 0.10 * ctx.aperture)
    return Skeleton.of(
        Stroke.from_points(
            "bowl",
            [(rx * 1.6, ry * 0.25), (rx, 0.0), (0.0, ry), (rx, 2 * ry), (rx * 1.6, ry * 1.75)],
        )
    )


def skeleton_u(ctx: DesignContext) -> Skeleton:
    w = _counter_width(ctx)
    return Skeleton.of(
        Stroke.from_points("left", [(0.0, ctx.x_height), (0.0, w * 0.3)]),
        Stroke.from_points("bottom", [(0.0, w * 0.3), (w / 2.0, -ctx.overshoot), (w, w * 0.3)]),
        Stroke.from_points("right", [(w, w * 0.3), (w, ctx.x_height)]),
    )


# --- continuous-curve letter builders ---------------------------------------


def skel_l(ctx: DesignContext, **opts: object) -> ComposedGlyph:
    """Ascender stem; optional pen-expand path via ``trace_letter`` if requested."""
    del opts
    return _assemble(ctx, vertical_stem(ctx, 0.0, 0.0, ctx.ascender), blend=False)


def skel_i(ctx: DesignContext, **opts: object) -> ComposedGlyph:
    """Stem with flat top + rounded-square tittle (no hollow ring / deep shear)."""
    del opts
    t = ctx.stem
    # Rectangle stem already ends flat at x-height — no knife notch.
    stem = vertical_stem(ctx, 0.0, 0.0, ctx.x_height)
    dot = tittle(ctx, t / 2.0, ctx.x_height + t * 0.55)
    # Disjoint parts: pack as two solids (union of distant shapes is fragile).
    return GlyphAssembler(ctx).add(stem).add(dot).build()


def skel_n(ctx: DesignContext, **opts: object) -> ComposedGlyph:
    """Left stem + continuous cubic arch + right stem; shoulder blend."""
    blend = opts.get("blend", True)
    w = _counter_width(ctx)
    t = ctx.stem
    # arch() expects inner faces of stems
    x_left, x_right = t, t + w
    left = vertical_stem(ctx, 0.0, 0.0, ctx.x_height)
    right = vertical_stem(ctx, x_right, 0.0, ctx.x_height * 0.58)
    shoulder = _continuous_arch(
        ctx,
        x_left,
        x_right,
        ctx.x_height * 0.48,
        ctx.x_height + ctx.overshoot,
    )
    return _assemble(ctx, left, right, shoulder, blend=blend)  # type: ignore[arg-type]


def skel_h(ctx: DesignContext, **opts: object) -> ComposedGlyph:
    """Ascender left stem + continuous arch + right stem; shoulder blend."""
    blend = opts.get("blend", True)
    w = _counter_width(ctx)
    t = ctx.stem
    x_left, x_right = t, t + w
    left = vertical_stem(ctx, 0.0, 0.0, ctx.ascender)
    right = vertical_stem(ctx, x_right, 0.0, ctx.x_height * 0.58)
    shoulder = _continuous_arch(
        ctx,
        x_left,
        x_right,
        ctx.x_height * 0.48,
        ctx.x_height + ctx.overshoot,
    )
    return _assemble(ctx, left, right, shoulder, blend=blend)  # type: ignore[arg-type]


def skel_o(ctx: DesignContext, **opts: object) -> ComposedGlyph:
    """Superellipse bowl with overshoot; continuous cubics (no polyline ring)."""
    del opts
    ry = ctx.x_height / 2.0 + ctx.overshoot
    rx = ry * (0.88 + 0.10 * ctx.aperture)
    cx, cy = rx, ctx.x_height / 2.0
    outer, hole = bowl(
        ctx,
        cx,
        cy,
        rx=rx,
        ry=ry,
        thickness=ctx.stem,
        shape="superellipse",
        n=_superellipse_n(ctx),
    )
    return _assemble(ctx, outer, holes=(hole,), blend=False, subtract_holes=True)


def skel_c(ctx: DesignContext, **opts: object) -> ComposedGlyph:
    """Open bowl: superellipse ring with aperture bite; shallow shear terminals."""
    del opts
    from typekernel.parts.aperture import open_bowl_ring

    ry = ctx.x_height / 2.0 + ctx.overshoot
    rx = ry * (0.88 + 0.10 * ctx.aperture)
    cx, cy = rx, ctx.x_height / 2.0
    outer, hole = bowl(
        ctx,
        cx,
        cy,
        rx=rx,
        ry=ry,
        thickness=ctx.stem,
        shape="superellipse",
        n=_superellipse_n(ctx),
    )
    # Aperture opens to the right; amount from ctx.aperture
    amount = rx * (0.22 + 0.28 * ctx.aperture)
    opened = open_bowl_ring(outer, hole, "right", amount, ctx)
    shear = _shallow_shear_deg(ctx)
    # Mild shear near upper / lower mouth (not deep notches).
    y_hi = cy + ry * 0.55
    y_lo = cy - ry * 0.55
    opened = shear_end(opened, (cx + rx * 0.85, y_hi), shear, along="x", band=ctx.stem * 0.9)
    opened = shear_end(opened, (cx + rx * 0.85, y_lo), -shear, along="x", band=ctx.stem * 0.9)
    return _assemble(ctx, opened, blend=False)


def skel_u(ctx: DesignContext, **opts: object) -> ComposedGlyph:
    """Continuous U-trough (cubic bottom); optional blend at trough corners."""
    blend = opts.get("blend", True)
    w = _counter_width(ctx)
    t = ctx.stem
    trough = u_bowl(
        ctx,
        0.0,
        t + w + t,
        ctx.x_height,
        -ctx.overshoot,
    )
    return _assemble(ctx, trough, blend=blend)  # type: ignore[arg-type]


SKEL_BUILDERS: Mapping[str, Callable[..., ComposedGlyph]] = {
    "l": skel_l,
    "i": skel_i,
    "n": skel_n,
    "h": skel_h,
    "o": skel_o,
    "c": skel_c,
    "u": skel_u,
}


def build_skel_letter(ch: str, ctx: DesignContext, **opts: object) -> ComposedGlyph:
    """Build one lowercase recipe; ``KeyError`` if unsupported."""
    key = ch.lower()
    try:
        builder = SKEL_BUILDERS[key]
    except KeyError as exc:
        raise KeyError(
            f"no skeleton recipe for {ch!r}; have {sorted(SKEL_BUILDERS)}"
        ) from exc
    return builder(ctx, **opts)


def build_skel_word(
    text: str,
    ctx: DesignContext,
    **opts: object,
) -> list[ComposedGlyph]:
    """Build each character with the shared context."""
    return [build_skel_letter(ch, ctx, **opts) for ch in text]
