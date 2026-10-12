"""Latin lowercase recipes built from shared parts (demo family).

All letters take the same :class:`~typekernel.parts.context.DesignContext` so
stem, contrast, overshoot and spacing stay in one rhythm — the point of the
parts layer versus one-off hard paths.

Boolean union is used only where overlaps are simple (``z`` bars + diagonal).
For ``a``, solids stay as separate parts plus a counter hole: unioning a bowl
into a stem that crosses the counter tends to shatter the ring in pathops.
"""

from __future__ import annotations

from typekernel.parts.compose import ComposedGlyph, GlyphAssembler
from typekernel.parts.context import DesignContext
from typekernel.parts.primitives import (
    bowl,
    stroke_polyline,
    tittle,
    u_bowl,
    vertical_stem,
)


def letter_z(ctx: DesignContext) -> ComposedGlyph:
    """Geometric ``z``: continuous Z spine stroked at ``ctx.stem``."""
    width = ctx.x_height * 0.76
    t = ctx.stem
    top = ctx.x_height
    spine = [
        (t * 0.2, top - t / 2.0),
        (width - t * 0.2, top - t / 2.0),
        (t * 0.2, t / 2.0),
        (width - t * 0.2, t / 2.0),
    ]
    body = stroke_polyline(ctx, spine, join_radius=ctx.join_radius * 0.85)
    return GlyphAssembler(ctx).add(body).build()


def letter_a(ctx: DesignContext) -> ComposedGlyph:
    """Single-story geometric ``a``: bowl + right stem + counter (no union).

    The stem sits *inside* the counter on the right so the punched hole leaves a
    clean vertical (classic single-story construction). Do not union bowl+stem:
    pathops tends to shatter the ring when the stem crosses the counter.
    """
    ry = ctx.x_height / 2.0 + ctx.overshoot
    rx = ry * 0.92
    cx = rx
    cy = ctx.x_height / 2.0
    outer, hole = bowl(ctx, cx, cy, rx=rx, ry=ry)
    # Stem hugs the right of the bowl and extends past the outer rim so a full
    # vertical reads after the counter is punched.
    stem_left = cx + rx - ctx.stem * 0.9
    stem = vertical_stem(
        ctx,
        stem_left,
        0.0,
        ctx.x_height + ctx.overshoot * 0.2,
    )
    return (
        GlyphAssembler(ctx)
        .add(outer)
        .add(stem)
        .add_hole(hole)
        .build()
    )


def letter_y(ctx: DesignContext) -> ComposedGlyph:
    """Geometric ``y``: continuous V + descender stroke."""
    width = ctx.x_height * 0.80
    top = ctx.x_height
    t = ctx.stem
    jx = width * 0.50
    jy = t * 0.45
    # Left arm alone, then right arm into descender as one stroke so the crotch joins.
    left = stroke_polyline(
        ctx,
        [(t * 0.7, top - t * 0.35), (jx, jy)],
        join_radius=0.0,
    )
    right = stroke_polyline(
        ctx,
        [
            (width - t * 0.7, top - t * 0.35),
            (jx, jy),
            (jx + t * 0.55, ctx.descender + t * 0.4),
        ],
        join_radius=ctx.join_radius * 0.9,
    )
    return GlyphAssembler(ctx).add(left).add(right).build()


def letter_j(ctx: DesignContext) -> ComposedGlyph:
    """Geometric ``j``: stroked stem + left hook, plus tittle."""
    import math

    cx = ctx.stem * 1.35
    t = ctx.stem
    hr = abs(ctx.descender) * 0.52
    bend_r = max(hr - t / 2.0, t * 0.8)
    # Center of bend sits left of the stem so the hook opens leftward.
    bend_cx = cx - bend_r
    bend_cy = ctx.descender + hr
    pts: list[tuple[float, float]] = [(cx, ctx.x_height - t / 2.0), (cx, bend_cy)]
    for i in range(1, 17):
        ang = math.radians(-100.0 * i / 16.0)  # east → past south toward west
        pts.append((bend_cx + bend_r * math.cos(ang), bend_cy + bend_r * math.sin(ang)))
    body = stroke_polyline(ctx, pts, join_radius=0.0)
    gap = t * 0.55
    dot = tittle(ctx, cx, ctx.x_height + gap)
    return GlyphAssembler(ctx).add(body).add(dot).build()


def letter_u(ctx: DesignContext) -> ComposedGlyph:
    """Geometric ``u``: single U-bowl part (two stems + rounded bottom)."""
    counter = ctx.x_height * 0.50
    x_left = 0.0
    x_right = ctx.stem + counter + ctx.stem
    trough = u_bowl(ctx, x_left, x_right, ctx.x_height, -ctx.overshoot)
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
