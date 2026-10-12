"""Latin lowercase recipes built from shared parts (demo family).

All letters take the same :class:`~typekernel.parts.context.DesignContext` so
stem, contrast, overshoot and spacing stay in one rhythm — the point of the
parts layer versus one-off hard paths.

Where boolean ops are available (``typekernel[boolean]``), recipes prefer
union + difference so joins and counters are single outlines. Without pathops,
they fall back to separate solids + holes (still drawable).
"""

from __future__ import annotations

import importlib.util

from typekernel.parts.compose import ComposedGlyph, GlyphAssembler
from typekernel.parts.context import DesignContext
from typekernel.parts.primitives import (
    arch,
    bowl,
    crossbar,
    fillet_pad,
    rounded_rect,
    stroke_polyline,
    tittle,
    u_bowl,
    vertical_stem,
)

_HAS_PATHOPS = importlib.util.find_spec("pathops") is not None


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
    """Single-story geometric ``a`` with fillet pads and robust boolean join.

    Construction:
      1. elliptical bowl outer + right stem + NE/SE fillet pads at the join
      2. boolean-union solids (when pathops is available)
      3. boolean-difference the counter (keeps a clean ring + stem)

    Without pathops: solids stay separate and the counter remains a hole.
    """
    ry = ctx.x_height / 2.0 + ctx.overshoot
    rx = ry * 0.92
    cx = rx
    cy = ctx.x_height / 2.0
    outer, hole = bowl(ctx, cx, cy, rx=rx, ry=ry)
    stem_left = cx + rx - ctx.stem * 0.9
    stem = vertical_stem(
        ctx,
        stem_left,
        0.0,
        ctx.x_height + ctx.overshoot * 0.2,
    )
    # Fillet pads at the stem/bowl concave notches (inside the join).
    r = ctx.join_radius * 0.85
    # Join sits near the right of the bowl; pads face into the counter side.
    join_x = stem_left
    pad_ne = fillet_pad(ctx, join_x, cy + ry * 0.15, radius=r, quadrant=1)  # NW into bowl
    pad_se = fillet_pad(ctx, join_x, cy - ry * 0.15, radius=r, quadrant=2)  # SW into bowl

    asm = GlyphAssembler(ctx).add(outer).add(stem).add(pad_ne).add(pad_se)
    if _HAS_PATHOPS:
        return asm.union_solids().add_hole(hole).subtract_holes().build()
    return asm.add_hole(hole).build()


def letter_y(ctx: DesignContext) -> ComposedGlyph:
    """Geometric ``y``: continuous V + descender stroke."""
    width = ctx.x_height * 0.80
    top = ctx.x_height
    t = ctx.stem
    jx = width * 0.50
    jy = t * 0.45
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
    asm = GlyphAssembler(ctx).add(left).add(right)
    if _HAS_PATHOPS:
        return asm.union_solids().build()
    return asm.build()


def letter_j(ctx: DesignContext) -> ComposedGlyph:
    """Geometric ``j``: stroked stem + left hook, plus tittle."""
    import math

    cx = ctx.stem * 1.35
    t = ctx.stem
    hr = abs(ctx.descender) * 0.52
    bend_r = max(hr - t / 2.0, t * 0.8)
    bend_cx = cx - bend_r
    bend_cy = ctx.descender + hr
    pts: list[tuple[float, float]] = [(cx, ctx.x_height - t / 2.0), (cx, bend_cy)]
    for i in range(1, 17):
        ang = math.radians(-100.0 * i / 16.0)
        pts.append((bend_cx + bend_r * math.cos(ang), bend_cy + bend_r * math.sin(ang)))
    body = stroke_polyline(ctx, pts, join_radius=0.0)
    gap = t * 0.55
    dot = tittle(ctx, cx, ctx.x_height + gap)
    return GlyphAssembler(ctx).add(body).add(dot).build()


def letter_u(ctx: DesignContext) -> ComposedGlyph:
    """Geometric ``u``: single U-bowl part (two stems + rounded bottom)."""
    counter_w = ctx.x_height * 0.50
    x_left = 0.0
    x_right = ctx.stem + counter_w + ctx.stem
    trough = u_bowl(ctx, x_left, x_right, ctx.x_height, -ctx.overshoot)
    return GlyphAssembler(ctx).add(trough).build()


def letter_n(ctx: DesignContext) -> ComposedGlyph:
    """Geometric ``n``: left stem + arch shoulder + right stem (unioned)."""
    counter_w = ctx.x_height * 0.48
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
    # Soften stem/arch joins with fillet pads.
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
    rx = ry * 0.96
    cx, cy = rx, ctx.x_height / 2.0
    outer, hole = bowl(ctx, cx, cy, rx=rx, ry=ry, thickness=ctx.stem)
    asm = GlyphAssembler(ctx).add(outer).add_hole(hole)
    if _HAS_PATHOPS:
        return asm.subtract_holes().build()
    return asm.build()


def letter_e(ctx: DesignContext) -> ComposedGlyph:
    """Geometric ``e``: bowl + crossbar; aperture opens to the right.

    Stub-quality: outer ring with a horizontal bar; the right gap is made by
    subtracting a wedge-like open mouth from the outer when pathops is present,
    otherwise the bar simply sits inside a full counter hole (less open).
    """
    ry = ctx.x_height / 2.0 + ctx.overshoot
    rx = ry * 0.95
    cx, cy = rx, ctx.x_height / 2.0
    outer, hole = bowl(ctx, cx, cy, rx=rx, ry=ry, thickness=ctx.stem * 0.95)
    bar_y = cy + ctx.stem * 0.05
    # Crossbar spans most of the counter; aperture shortens the right end.
    gap = ctx.aperture * rx * 0.55
    bar = crossbar(
        ctx,
        cx - (rx - ctx.stem) + ctx.stem * 0.1,
        cx + (rx - ctx.stem) - gap,
        bar_y,
        thickness=ctx.thin,
    )
    asm = GlyphAssembler(ctx).add(outer).add(bar).add_hole(hole)
    if _HAS_PATHOPS:
        return asm.union_solids().subtract_holes().build()
    return asm.build()


def letter_s(ctx: DesignContext) -> ComposedGlyph:
    """Geometric ``s`` stub: stroked S-spine (agents refine with bowls later)."""
    w = ctx.x_height * 0.62
    t = ctx.stem * 0.92
    top = ctx.x_height
    # Approximate S with a polyline spine; soft joins from roundness.
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
    rx = ry * 0.94
    cx, cy = rx, ctx.x_height / 2.0
    outer, hole = bowl(ctx, cx, cy, rx=rx, ry=ry)
    # Aperture: rectangular bite on the right.
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
    gap = ctx.stem * 0.55
    dot = tittle(ctx, ctx.stem / 2.0, ctx.x_height + gap)
    return GlyphAssembler(ctx).add(stem).add(dot).build()


def letter_l(ctx: DesignContext) -> ComposedGlyph:
    """Geometric ``l``: ascending stem."""
    stem = vertical_stem(ctx, 0.0, 0.0, ctx.ascender)
    return GlyphAssembler(ctx).add(stem).build()


def letter_h(ctx: DesignContext) -> ComposedGlyph:
    """Geometric ``h``: ascending left stem + arch + right stem."""
    counter_w = ctx.x_height * 0.48
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
