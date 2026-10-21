"""Latin lowercase recipes built from shared parts (demo family).

.. deprecated::
    Experimental demo recipes. Prefer :class:`~typekernel.parts.family.FormSources`
    and ``RELATED_FORMS`` for production families.

All letters take the same :class:`~typekernel.parts.context.DesignContext` so
stem, contrast, overshoot and spacing stay in one rhythm — the point of the
parts layer versus one-off hard paths.

Where boolean ops are available (``typekernel[boolean]``), recipes prefer
union + difference so joins and counters are single outlines. Without pathops,
they fall back to separate solids + holes (still drawable).
"""

from __future__ import annotations

import importlib.util

from typekernel.parts.compose import ComposedGlyph, GlyphAssembler, try_difference, try_union
from typekernel.parts.context import DesignContext
from typekernel.parts.primitives import (
    arch,
    bowl,
    crossbar,
    fillet_pad,
    rounded_rect,
    smooth_hook,
    stroke_polyline,
    tittle,
    u_bowl,
    vertical_stem,
)

_HAS_PATHOPS = importlib.util.find_spec("pathops") is not None




def letter_z(ctx: DesignContext) -> ComposedGlyph:
    """Geometric ``z``: sharp Z spine, then G2 corner blends at both bends.

    Spine is stroked with mitred joins; :meth:`GlyphAssembler.blend_joins`
    replaces the mitres with curvature-continuous turns. Bar ends stay flat.
    """
    width = ctx.x_height * (0.72 + 0.08 * ctx.aperture)
    t = ctx.stem
    top = ctx.x_height
    spine = [
        (t * 0.15, top - t / 2.0),
        (width - t * 0.15, top - t / 2.0),
        (t * 0.15, t / 2.0),
        (width - t * 0.15, t / 2.0),
    ]
    body = stroke_polyline(ctx, spine, join_radius=0.0)
    return GlyphAssembler(ctx).add(body).blend_joins(ctx.join_radius * 0.9).ease_curvature().build()


def letter_a(ctx: DesignContext) -> ComposedGlyph:
    """Single-story ``a``: bowl + right stem, crotches blended (no fillet pads).

    Union and counter subtraction set the topology; ``blend_joins`` turns the
    stem-to-bowl crotches into continuous curves.
    """
    ry = ctx.x_height / 2.0 + ctx.overshoot
    rx = ry * (0.88 + 0.06 * ctx.aperture)
    cx = rx
    cy = ctx.x_height / 2.0
    bowl_t = ctx.stem * (0.92 + 0.04 * (1.0 - ctx.aperture))
    outer, hole = bowl(ctx, cx, cy, rx=rx, ry=ry, thickness=bowl_t)
    stem_left = cx + rx - ctx.stem * 0.88
    stem = vertical_stem(ctx, stem_left, 0.0, ctx.x_height + ctx.overshoot * 0.2)
    asm = GlyphAssembler(ctx).add(outer).add(stem)
    if _HAS_PATHOPS:
        return (
            asm.union_solids()
            .add_hole(hole)
            .subtract_holes()
            .blend_joins(ctx.join_radius * 0.8)
            .ease_curvature()
            .build()
        )
    return asm.add_hole(hole).build()


def letter_y(ctx: DesignContext) -> ComposedGlyph:
    """Geometric ``y``: V + right-leg descender, crotch and bend blended."""
    width = ctx.x_height * (0.76 + 0.06 * ctx.aperture)
    top = ctx.x_height
    t = ctx.stem
    jx = width * 0.50
    jy = t * 0.40
    left = stroke_polyline(ctx, [(t * 0.65, top - t * 0.30), (jx, jy)], join_radius=0.0)
    right = stroke_polyline(
        ctx,
        [
            (width - t * 0.65, top - t * 0.30),
            (jx, jy),
            (jx + t * 0.50, ctx.descender + t * 0.35),
        ],
        join_radius=0.0,
    )
    asm = GlyphAssembler(ctx).add(left).add(right)
    if _HAS_PATHOPS:
        return asm.union_solids().blend_joins(ctx.join_radius * 0.6).ease_curvature().build()
    return asm.build()


def letter_j(ctx: DesignContext) -> ComposedGlyph:
    """Geometric ``j``: stem → one continuous arc → flat tail, plus tittle."""
    t = ctx.stem
    x_right = t * 1.80
    body = smooth_hook(ctx, x_right, ctx.x_height, ctx.descender)
    dot = tittle(ctx, x_right - t / 2.0, ctx.x_height + t * 0.60)
    return GlyphAssembler(ctx).add(body).add(dot).ease_curvature().build()


def letter_u(ctx: DesignContext) -> ComposedGlyph:
    """Geometric ``u``: U-trough with open counter (already continuous)."""
    counter_w = ctx.x_height * (0.48 + 0.08 * ctx.aperture)
    x_right = ctx.stem + counter_w + ctx.stem
    trough = u_bowl(ctx, 0.0, x_right, ctx.x_height, -ctx.overshoot)
    return GlyphAssembler(ctx).add(trough).ease_curvature().build()


def letter_n(ctx: DesignContext) -> ComposedGlyph:
    """Geometric ``n``: left stem + arch shoulder + right stem (unioned)."""
    counter_w = ctx.x_height * 0.52
    x0 = 0.0
    x1 = ctx.stem
    x2 = x1 + counter_w
    left = vertical_stem(ctx, x0, 0.0, ctx.x_height)
    right = vertical_stem(ctx, x2, 0.0, ctx.x_height * 0.55)
    shoulder = arch(
        ctx,
        x1,
        x2,
        ctx.x_height * 0.45,
        ctx.x_height + ctx.overshoot,
    )
    r = ctx.join_radius * 0.7
    pad_l = fillet_pad(ctx, x1, ctx.x_height * 0.55, radius=r, quadrant=0)
    pad_r = fillet_pad(ctx, x2, ctx.x_height * 0.55, radius=r, quadrant=1)
    asm = GlyphAssembler(ctx).add(left).add(right).add(shoulder).add(pad_l).add(pad_r)
    if _HAS_PATHOPS:
        return asm.union_solids().build()
    return asm.build()


def letter_o(ctx: DesignContext) -> ComposedGlyph:
    """Geometric ``o``: elliptical bowl with counter (difference when possible)."""
    ry = ctx.x_height / 2.0 + ctx.overshoot
    rx = ry * 0.98
    cx, cy = rx, ctx.x_height / 2.0
    outer, hole = bowl(ctx, cx, cy, rx=rx, ry=ry, thickness=ctx.stem)
    asm = GlyphAssembler(ctx).add(outer).add_hole(hole)
    if _HAS_PATHOPS:
        return asm.subtract_holes().build()
    return asm.build()


def letter_e(ctx: DesignContext) -> ComposedGlyph:
    """Geometric ``e``: ring + full crossbar; aperture opens below the bar."""
    ry = ctx.x_height / 2.0 + ctx.overshoot
    rx = ry * 0.96
    cx, cy = rx, ctx.x_height / 2.0
    t = ctx.stem * 0.95
    outer, hole = bowl(ctx, cx, cy, rx=rx, ry=ry, thickness=t)
    bar_y = cy + ctx.stem * 0.05
    bar = crossbar(ctx, cx - rx + t * 0.5, cx + rx - t * 0.5, bar_y, thickness=ctx.thin)
    if not _HAS_PATHOPS:
        return GlyphAssembler(ctx).add(outer).add(bar).add_hole(hole).build()
    # Cut the counter before adding the bar, or the counter swallows the bar.
    ring = try_difference(outer, hole)
    body = try_union([ring, bar])
    bar_bottom = bar_y - ctx.thin / 2.0
    gap_h = ctx.x_height * (0.10 + 0.16 * ctx.aperture)
    bite = rounded_rect(
        ctx,
        cx + (rx - t) * 0.2,
        bar_bottom - gap_h,
        cx + rx + ctx.stem,
        bar_bottom,
        radius=0.0,
    )
    return GlyphAssembler(ctx).add(try_difference(body, bite)).build()


def letter_s(ctx: DesignContext) -> ComposedGlyph:
    """Geometric ``s`` stub: stroked S-spine (agents refine with bowls later)."""
    w = ctx.x_height * 0.62
    t = ctx.stem * 0.95
    top = ctx.x_height
    spine = [
        (w * 0.85, top - t * 0.3),
        (w * 0.25, top - t * 0.3),
        (w * 0.20, top * 0.72),
        (w * 0.55, top * 0.55),
        (w * 0.80, top * 0.38),
        (w * 0.75, t * 1.1),
        (w * 0.15, t * 0.35),
    ]
    body = stroke_polyline(ctx, spine, width=t, join_radius=ctx.join_radius)
    return GlyphAssembler(ctx).add(body).build()


def letter_c(ctx: DesignContext) -> ComposedGlyph:
    """Geometric ``c``: open bowl (counter + right aperture cut)."""
    ry = ctx.x_height / 2.0 + ctx.overshoot
    rx = ry * 0.96
    cx, cy = rx, ctx.x_height / 2.0
    outer, hole = bowl(ctx, cx, cy, rx=rx, ry=ry)
    gap_w = ctx.aperture * rx * 0.70
    gap_h = ctx.x_height * (0.35 + 0.25 * ctx.aperture)
    bite = rounded_rect(
        ctx,
        cx + rx - gap_w,
        cy - gap_h / 2.0,
        cx + rx + ctx.stem,
        cy + gap_h / 2.0,
        radius=ctx.join_radius * 0.3,
    )
    asm = GlyphAssembler(ctx).add(outer).add_hole(hole).add_hole(bite)
    if _HAS_PATHOPS:
        return asm.subtract_holes().build()
    return asm.build()


def letter_i(ctx: DesignContext) -> ComposedGlyph:
    """Geometric ``i``: stem + tittle."""
    stem = vertical_stem(ctx, 0.0, 0.0, ctx.x_height)
    gap = ctx.stem * 0.70
    dot = tittle(ctx, ctx.stem / 2.0, ctx.x_height + gap)
    return GlyphAssembler(ctx).add(stem).add(dot).build()


def letter_l(ctx: DesignContext) -> ComposedGlyph:
    """Geometric ``l``: ascending stem."""
    stem = vertical_stem(ctx, 0.0, 0.0, ctx.ascender)
    return GlyphAssembler(ctx).add(stem).build()


def letter_h(ctx: DesignContext) -> ComposedGlyph:
    """Geometric ``h``: ascending left stem + arch + right stem."""
    counter_w = ctx.x_height * 0.52
    x0 = 0.0
    x1 = ctx.stem
    x2 = x1 + counter_w
    left = vertical_stem(ctx, x0, 0.0, ctx.ascender)
    right = vertical_stem(ctx, x2, 0.0, ctx.x_height * 0.55)
    shoulder = arch(ctx, x1, x2, ctx.x_height * 0.45, ctx.x_height + ctx.overshoot)
    asm = GlyphAssembler(ctx).add(left).add(right).add(shoulder)
    if _HAS_PATHOPS:
        return asm.union_solids().build()
    return asm.build()


LETTER_BUILDERS = {
    "a": letter_a,
    "c": letter_c,
    "e": letter_e,
    "h": letter_h,
    "i": letter_i,
    "j": letter_j,
    "l": letter_l,
    "n": letter_n,
    "o": letter_o,
    "s": letter_s,
    "u": letter_u,
    "y": letter_y,
    "z": letter_z,
}


def build_letter(ch: str, ctx: DesignContext | None = None) -> ComposedGlyph:
    """Build one lowercase recipe by character; raises ``KeyError`` if missing."""
    ctx = ctx or DesignContext.geometric_sans()
    return LETTER_BUILDERS[ch](ctx)


def build_word(text: str, ctx: DesignContext | None = None) -> list[ComposedGlyph]:
    """Build each lowercase letter in ``text`` with one shared context."""
    ctx = ctx or DesignContext.geometric_sans()
    return [LETTER_BUILDERS[ch](ctx) for ch in text]


def word_zayju(ctx: DesignContext | None = None) -> list[ComposedGlyph]:
    """Build ``zayju`` with one shared context (family rhythm)."""
    return build_word("zayju", ctx)
