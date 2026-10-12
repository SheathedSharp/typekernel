"""Latin lowercase recipes built from shared parts (demo family).

All letters take the same :class:`~typekernel.parts.context.DesignContext` so
stem, contrast, overshoot and spacing stay in one rhythm — the point of the
parts layer versus one-off hard paths.
"""

from __future__ import annotations

from typekernel.parts.compose import ComposedGlyph, GlyphAssembler
from typekernel.parts.context import DesignContext
from typekernel.parts.primitives import (
    bowl,
    diagonal_stem,
    hook_terminal,
    horizontal_bar,
    tittle,
    u_bowl,
    vertical_stem,
)


def letter_z(ctx: DesignContext) -> ComposedGlyph:
    """Geometric ``z``: top bar + diagonal + bottom bar, boolean-unioned."""
    width = ctx.x_height * 0.78
    top = horizontal_bar(ctx, 0.0, width, ctx.x_height - ctx.thin)
    bot = horizontal_bar(ctx, 0.0, width, 0.0)
    # Diagonal connects inner corners so bars and stem share even colour.
    x0 = width - ctx.stem * 0.35
    y0 = ctx.x_height - ctx.thin * 0.5
    x1 = ctx.stem * 0.35
    y1 = ctx.thin * 0.5
    diag = diagonal_stem(ctx, x0, y0, x1, y1)
    return (
        GlyphAssembler(ctx)
        .add(top)
        .add(diag)
        .add(bot)
        .union_solids()
        .build()
    )


def letter_a(ctx: DesignContext) -> ComposedGlyph:
    """Single-story geometric ``a``: bowl + right stem, counter hole."""
    ry = ctx.x_height / 2.0 + ctx.overshoot
    rx = ry * 0.94
    cx = rx
    cy = ctx.x_height / 2.0
    outer, hole = bowl(ctx, cx, cy, rx=rx, ry=ry)
    # Stem sits on the right of the bowl, reaching baseline to slight overshoot.
    stem_left = cx + rx - ctx.stem * 1.05
    stem = vertical_stem(
        ctx,
        stem_left,
        0.0,
        ctx.x_height + ctx.overshoot * 0.25,
    )
    return (
        GlyphAssembler(ctx)
        .add(outer)
        .add(stem)
        .add_hole(hole)
        .union_solids()
        .build()
    )


def letter_y(ctx: DesignContext) -> ComposedGlyph:
    """Geometric ``y``: V crotch + descending right leg."""
    width = ctx.x_height * 0.82
    top = ctx.x_height
    jx = width * 0.48
    jy = ctx.stem * 0.35
    left = diagonal_stem(
        ctx,
        ctx.stem * 0.55,
        top - ctx.stem * 0.35,
        jx,
        jy,
    )
    right = diagonal_stem(
        ctx,
        width - ctx.stem * 0.55,
        top - ctx.stem * 0.35,
        jx + ctx.stem * 0.15,
        jy,
    )
    # Descender continues the right arm's direction.
    leg = diagonal_stem(
        ctx,
        jx + ctx.stem * 0.15,
        jy,
        jx + ctx.stem * 0.85,
        ctx.descender + ctx.stem * 0.35,
    )
    return (
        GlyphAssembler(ctx)
        .add(left)
        .add(right)
        .add(leg)
        .union_solids()
        .build()
    )


def letter_j(ctx: DesignContext) -> ComposedGlyph:
    """Geometric ``j``: hook terminal + tittle, shared stem width."""
    cx = ctx.stem * 1.15
    hook = hook_terminal(ctx, cx, ctx.x_height, ctx.descender)
    gap = ctx.stem * 0.55
    dot = tittle(ctx, cx, ctx.x_height + gap)
    return GlyphAssembler(ctx).add(hook).add(dot).build()


def letter_u(ctx: DesignContext) -> ComposedGlyph:
    """Geometric ``u``: single U-bowl part (two stems + rounded bottom)."""
    counter = ctx.x_height * 0.52
    x_left = 0.0
    x_right = ctx.stem + counter + ctx.stem
    trough = u_bowl(
        ctx,
        x_left,
        x_right,
        ctx.x_height,
        -ctx.overshoot,
    )
    return GlyphAssembler(ctx).add(trough).build()


LETTER_BUILDERS = {
    "z": letter_z,
    "a": letter_a,
    "y": letter_y,
    "j": letter_j,
    "u": letter_u,
}


def word_zayju(ctx: DesignContext | None = None) -> list[ComposedGlyph]:
    """Build ``zayju`` with one shared context (family rhythm)."""
    ctx = ctx or DesignContext.geometric_sans()
    return [LETTER_BUILDERS[ch](ctx) for ch in "zayju"]
