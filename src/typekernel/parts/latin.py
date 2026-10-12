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

from typekernel.geo.contour import Contour
from typekernel.geo.path_builder import PathBuilder
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
    vertical_stem,
)

_HAS_PATHOPS = importlib.util.find_spec("pathops") is not None




def letter_z(ctx: DesignContext) -> ComposedGlyph:
    """Neo-grotesque ``z`` — continuous cubic outline (scaled reference).

    Coordinates are authored at a reference x-height of 1080 and scaled by
    ``ctx.x_height / 1080``. Topology is continuous closed cubics (TrueType
    source elevated with Qu2Cu), not boolean-assembled parts.
    """
    s = ctx.x_height / 1080.0
    b = PathBuilder()
    b.moveTo(917.0000 * s, 159.0000 * s)
    b.lineTo(917.0000 * s, 0.0000 * s)
    b.lineTo(92.0000 * s, 0.0000 * s)
    b.lineTo(92.0000 * s, 133.0000 * s)
    b.lineTo(709.0000 * s, 973.0000 * s)
    b.lineTo(728.0000 * s, 921.0000 * s)
    b.lineTo(112.0000 * s, 921.0000 * s)
    b.lineTo(112.0000 * s, 1080.0000 * s)
    b.lineTo(907.0000 * s, 1080.0000 * s)
    b.lineTo(907.0000 * s, 947.0000 * s)
    b.lineTo(290.0000 * s, 107.0000 * s)
    b.lineTo(255.0000 * s, 159.0000 * s)
    b.closePath()
    outline = b.build()
    return GlyphAssembler(ctx).add(outline).build()


def letter_a(ctx: DesignContext) -> ComposedGlyph:
    """Neo-grotesque ``a`` — continuous cubic outline (scaled reference).

    Coordinates are authored at a reference x-height of 1080 and scaled by
    ``ctx.x_height / 1080``. Topology is continuous closed cubics (TrueType
    source elevated with Qu2Cu), not boolean-assembled parts.
    """
    s = ctx.x_height / 1080.0
    b = PathBuilder()
    b.moveTo(518.0000 * s, 1102.0000 * s)
    b.curveTo(679.3333 * s, 1102.0000 * s, 801.1667 * s, 1037.3333 * s, 864.5000 * s, 920.0000 * s)
    b.curveTo(896.1667 * s, 861.3333 * s, 912.0000 * s, 792.0000 * s, 912.0000 * s, 712.0000 * s)
    b.lineTo(912.0000 * s, 223.0000 * s)
    b.curveTo(912.0000 * s, 180.3333 * s, 930.6667 * s, 159.0000 * s, 972.0000 * s, 159.0000 * s)
    b.lineTo(1041.0000 * s, 159.0000 * s)
    b.lineTo(1041.0000 * s, 0.0000 * s)
    b.lineTo(945.0000 * s, 0.0000 * s)
    b.curveTo(908.3333 * s, 0.0000 * s, 875.6667 * s, 7.8333 * s, 847.0000 * s, 23.5000 * s)
    b.curveTo(789.6667 * s, 54.8333 * s, 755.0000 * s, 113.3333 * s, 755.0000 * s, 184.0000 * s)
    b.lineTo(755.0000 * s, 600.0000 * s)
    b.lineTo(731.0000 * s, 600.0000 * s)
    b.lineTo(731.0000 * s, 725.0000 * s)
    b.curveTo(731.0000 * s, 865.0000 * s, 652.6667 * s, 944.0000 * s, 514.0000 * s, 944.0000 * s)
    b.curveTo(392.6667 * s, 944.0000 * s, 315.3333 * s, 883.0000 * s, 302.0000 * s, 775.0000 * s)
    b.lineTo(133.0000 * s, 775.0000 * s)
    b.curveTo(138.3333 * s, 841.6667 * s, 157.5000 * s, 899.5000 * s, 190.5000 * s, 948.5000 * s)
    b.curveTo(256.5000 * s, 1046.5000 * s, 371.3333 * s, 1102.0000 * s, 518.0000 * s, 1102.0000 * s)
    b.closePath()
    b.moveTo(536.0000 * s, 655.0000 * s)
    b.lineTo(843.0000 * s, 682.0000 * s)
    b.lineTo(843.0000 * s, 524.0000 * s)
    b.lineTo(548.0000 * s, 498.0000 * s)
    b.curveTo(361.3333 * s, 482.0000 * s, 274.0000 * s, 424.0000 * s, 274.0000 * s, 300.0000 * s)
    b.curveTo(274.0000 * s, 192.0000 * s, 337.0000 * s, 136.0000 * s, 453.0000 * s, 136.0000 * s)
    b.curveTo(561.0000 * s, 136.0000 * s, 648.1667 * s, 196.1667 * s, 695.5000 * s, 299.5000 * s)
    b.curveTo(719.1667 * s, 351.1667 * s, 731.0000 * s, 410.0000 * s, 731.0000 * s, 476.0000 * s)
    b.lineTo(731.0000 * s, 600.0000 * s)
    b.lineTo(793.0000 * s, 600.0000 * s)
    b.lineTo(793.0000 * s, 384.0000 * s)
    b.curveTo(793.0000 * s, 308.0000 * s, 776.5000 * s, 239.0000 * s, 743.5000 * s, 177.0000 * s)
    b.curveTo(710.5000 * s, 115.0000 * s, 665.3333 * s, 66.3333 * s, 608.0000 * s, 31.0000 * s)
    b.curveTo(550.6667 * s, -4.3333 * s, 486.6667 * s, -22.0000 * s, 416.0000 * s, -22.0000 * s)
    b.curveTo(352.6667 * s, -22.0000 * s, 296.0000 * s, -8.5000 * s, 246.0000 * s, 18.5000 * s)
    b.curveTo(196.0000 * s, 45.5000 * s, 156.8333 * s, 83.1667 * s, 128.5000 * s, 131.5000 * s)
    b.curveTo(100.1667 * s, 179.8333 * s, 86.0000 * s, 235.0000 * s, 86.0000 * s, 297.0000 * s)
    b.curveTo(86.0000 * s, 401.6667 * s, 126.0000 * s, 484.3333 * s, 206.0000 * s, 545.0000 * s)
    b.curveTo(286.0000 * s, 605.6667 * s, 396.0000 * s, 642.3333 * s, 536.0000 * s, 655.0000 * s)
    b.closePath()
    outline = b.build()
    return GlyphAssembler(ctx).add(outline).build()


def letter_y(ctx: DesignContext) -> ComposedGlyph:
    """Neo-grotesque ``y`` — continuous cubic outline (scaled reference).

    Coordinates are authored at a reference x-height of 1080 and scaled by
    ``ctx.x_height / 1080``. Topology is continuous closed cubics (TrueType
    source elevated with Qu2Cu), not boolean-assembled parts.
    """
    s = ctx.x_height / 1080.0
    b = PathBuilder()
    b.moveTo(567.0000 * s, 141.0000 * s)
    b.lineTo(473.0000 * s, -68.0000 * s)
    b.lineTo(57.0000 * s, 1080.0000 * s)
    b.lineTo(250.0000 * s, 1080.0000 * s)
    b.closePath()
    b.moveTo(446.0000 * s, -480.0000 * s)
    b.lineTo(263.0000 * s, -480.0000 * s)
    b.lineTo(531.0000 * s, 141.0000 * s)
    b.lineTo(898.0000 * s, 1080.0000 * s)
    b.lineTo(1085.0000 * s, 1080.0000 * s)
    b.lineTo(635.0000 * s, -4.0000 * s)
    b.closePath()
    outline = b.build()
    if _HAS_PATHOPS and len(outline.contours) >= 2:
        from typekernel.geo.outline import Outline as _Outline
        from typekernel.parts.compose import try_union
        parts = [_Outline((c,)) for c in outline.contours]
        return GlyphAssembler(ctx).add(try_union(parts)).build()
    return GlyphAssembler(ctx).add(outline).build()


def letter_j(ctx: DesignContext) -> ComposedGlyph:
    """Neo-grotesque ``j`` — continuous cubic outline (scaled reference).

    Coordinates are authored at a reference x-height of 1080 and scaled by
    ``ctx.x_height / 1080``. Topology is continuous closed cubics (TrueType
    source elevated with Qu2Cu), not boolean-assembled parts.
    """
    s = ctx.x_height / 1080.0
    b = PathBuilder()
    b.moveTo(351.0000 * s, 1500.0000 * s)
    b.lineTo(351.0000 * s, 1220.0000 * s)
    b.lineTo(153.0000 * s, 1220.0000 * s)
    b.lineTo(153.0000 * s, 1500.0000 * s)
    b.closePath()
    b.moveTo(34.0000 * s, -480.0000 * s)
    b.lineTo(-54.0000 * s, -480.0000 * s)
    b.lineTo(-54.0000 * s, -321.0000 * s)
    b.lineTo(0.0000 * s, -321.0000 * s)
    b.curveTo(109.3333 * s, -321.0000 * s, 162.0000 * s, -268.0000 * s, 162.0000 * s, -160.0000 * s)
    b.lineTo(162.0000 * s, 1080.0000 * s)
    b.lineTo(342.0000 * s, 1080.0000 * s)
    b.lineTo(342.0000 * s, -187.0000 * s)
    b.curveTo(342.0000 * s, -301.6667 * s, 287.3333 * s, -393.6667 * s, 194.0000 * s, -443.0000 * s)
    b.curveTo(147.3333 * s, -467.6667 * s, 94.0000 * s, -480.0000 * s, 34.0000 * s, -480.0000 * s)
    b.closePath()
    outline = b.build()
    if len(outline.contours) >= 2:
        from typekernel.geo.outline import Outline as _Outline

        def _abs_area(c: Contour) -> float:
            pts = [seg.points[0] for seg in c.segments]
            if len(pts) < 3:
                return 0.0
            pts.append(c.segments[-1].points[-1])
            a = 0.0
            for i in range(len(pts) - 1):
                a += pts[i].x * pts[i + 1].y - pts[i + 1].x * pts[i].y
            return abs(a) * 0.5

        contours = sorted(outline.contours, key=_abs_area)
        tittle_o = _Outline((contours[0],))
        body_o = _Outline(tuple(contours[1:]))
        return GlyphAssembler(ctx).add(body_o).add(tittle_o).build()
    return GlyphAssembler(ctx).add(outline).build()


def letter_u(ctx: DesignContext) -> ComposedGlyph:
    """Neo-grotesque ``u`` — continuous cubic outline (scaled reference).

    Coordinates are authored at a reference x-height of 1080 and scaled by
    ``ctx.x_height / 1080``. Topology is continuous closed cubics (TrueType
    source elevated with Qu2Cu), not boolean-assembled parts.
    """
    s = ctx.x_height / 1080.0
    b = PathBuilder()
    b.moveTo(592.0000 * s, 140.0000 * s)
    b.curveTo(697.3333 * s, 140.0000 * s, 777.3333 * s, 184.3333 * s, 820.0000 * s, 263.0000 * s)
    b.curveTo(841.3333 * s, 302.3333 * s, 852.0000 * s, 348.6667 * s, 852.0000 * s, 402.0000 * s)
    b.lineTo(852.0000 * s, 1080.0000 * s)
    b.lineTo(1031.0000 * s, 1080.0000 * s)
    b.lineTo(1031.0000 * s, 396.0000 * s)
    b.curveTo(1031.0000 * s, 314.6667 * s, 1012.5000 * s, 242.3333 * s, 975.5000 * s, 179.0000 * s)
    b.curveTo(938.5000 * s, 115.6667 * s, 886.5000 * s, 66.3333 * s, 819.5000 * s, 31.0000 * s)
    b.curveTo(752.5000 * s, -4.3333 * s, 676.3333 * s, -22.0000 * s, 591.0000 * s, -22.0000 * s)
    b.curveTo(505.6667 * s, -22.0000 * s, 429.5000 * s, -4.3333 * s, 362.5000 * s, 31.0000 * s)
    b.curveTo(295.5000 * s, 66.3333 * s, 243.5000 * s, 115.6667 * s, 206.5000 * s, 179.0000 * s)
    b.curveTo(169.5000 * s, 242.3333 * s, 151.0000 * s, 314.6667 * s, 151.0000 * s, 396.0000 * s)
    b.lineTo(151.0000 * s, 1080.0000 * s)
    b.lineTo(332.0000 * s, 1080.0000 * s)
    b.lineTo(332.0000 * s, 402.0000 * s)
    b.curveTo(332.0000 * s, 295.3333 * s, 376.5000 * s, 214.6667 * s, 454.5000 * s, 172.0000 * s)
    b.curveTo(493.5000 * s, 150.6667 * s, 539.3333 * s, 140.0000 * s, 592.0000 * s, 140.0000 * s)
    b.closePath()
    outline = b.build()
    return GlyphAssembler(ctx).add(outline).build()


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
    """Geometric ``e``: bowl + crossbar; aperture opens to the right."""
    ry = ctx.x_height / 2.0 + ctx.overshoot
    rx = ry * 0.96
    cx, cy = rx, ctx.x_height / 2.0
    outer, hole = bowl(ctx, cx, cy, rx=rx, ry=ry, thickness=ctx.stem * 0.95)
    bar_y = cy + ctx.stem * 0.05
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
