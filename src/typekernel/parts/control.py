"""Control glyphs and related forms — type-designer workflow.

Order: proportions (:class:`~typekernel.parts.context.DesignContext`) →
control letters as **continuous cubic outlines** → derive related forms →
optical / class spacing (elsewhere).

Each control glyph is drawn from a design record (:class:`NMetrics` for the
``n`` family, :class:`OMetrics` for the ``o`` family) and carries it as
``ComposedGlyph.design``. Related forms read that record from the control
glyph, so tuning the control (``n_metrics(ctx).tuned(counter=...)``) carries
through to ``h``, ``u``, ``i``, ``l`` without touching the context.
"""

from __future__ import annotations

import math
from collections.abc import Callable
from dataclasses import dataclass, replace
from typing import Literal

from fontTools.misc.bezierTools import splitCubic

from typekernel.geo.contour import Contour, reverse_contour, signed_area
from typekernel.geo.curves import superellipse_cubics
from typekernel.geo.outline import Outline, bounds
from typekernel.geo.path_builder import PathBuilder
from typekernel.geo.path_helpers import KAPPA
from typekernel.geo.point import Point
from typekernel.geo.segment import CubicSegment, LineSegment
from typekernel.parts.compose import ComposedGlyph, GlyphAssembler
from typekernel.parts.context import DesignContext
from typekernel.parts.primitives import (
    bowl,
    contrast_stem_caps,
    tittle,
    vertical_stem,
)
from typekernel.parts.terminal_openings import (
    apply_terminal_shear,
    opening_closure,
    r_arm_scale,
    s_opening_factor,
)
from typekernel.parts.transforms import mirror_x, mirror_y, translate

__all__ = [
    "S_OPENING_REACH_RELIEF",
    "NMetrics",
    "OMetrics",
    "a_from_o",
    "b_from_o",
    "build_control_letter",
    "build_control_word",
    "build_h",
    "build_i",
    "build_m",
    "build_n",
    "build_o",
    "build_r",
    "build_u",
    "c_from_o",
    "d_from_o",
    "dotless_i_from_n",
    "dotless_j_from_n",
    "e_from_o",
    "f_from_n",
    "g_from_o",
    "h_from_n",
    "i_from_n",
    "j_from_n",
    "l_from_n",
    "m_from_n",
    "n_metrics",
    "o_metrics",
    "p_from_o",
    "q_from_o",
    "r_from_n",
    "s_from_o",
    "t_from_n",
    "u_from_n",
]

Pt = tuple[float, float]
Cubic = tuple[Pt, Pt, Pt, Pt]


@dataclass(frozen=True, slots=True)
class NMetrics:
    """Design record for the ``n`` family (``n h m r u i l``).

    Attributes:
        stem: Vertical stem thickness.
        counter: Inner face to inner face of the ``n`` counter.
        x_height: Flat top of the left stem.
        ascender: Top of ascending stems (``h``, ``l``).
        overshoot: How far round extrema pass the zones.
        crown_y: Outer shoulder peak.
        leg_top: Where the outer shoulder lands on the right leg.
        join_y: Inner crotch height where the counter springs from the stems.
        inner_crown: Counter peak under the shoulder (``crown_y - inner_crown``
            is the shoulder thickness).
        kappa: Shoulder handle ratio (tension).
    """

    stem: float
    counter: float
    x_height: float
    ascender: float
    overshoot: float
    crown_y: float
    leg_top: float
    join_y: float
    kappa: float
    inner_crown: float

    @property
    def shoulder_thickness(self) -> float:
        return self.crown_y - self.inner_crown

    @property
    def width(self) -> float:
        """Ink width of ``n``: two stems around one counter."""
        return 2.0 * self.stem + self.counter

    def tuned(self, **kwargs: float) -> NMetrics:
        """Copy with selected fields overridden (designer adjustment)."""
        return replace(self, **kwargs)


def n_metrics(ctx: DesignContext) -> NMetrics:
    """Derive the ``n`` design record from family proportions."""
    stem = ctx.stem
    counter = ctx.x_height * (0.46 + 0.12 * ctx.aperture)
    # Slightly flatter shoulder when roundness is low (coding); rounder when soft.
    kappa = KAPPA * (0.92 + 0.28 * ctx.roundness)
    crown_y = ctx.x_height + ctx.overshoot
    # Outer meet: just under x-height so crown overshoots; inner join lower.
    leg_top = ctx.x_height - stem * 0.02
    join_y = ctx.x_height * (0.50 + 0.04 * ctx.roundness)
    inner_crown = crown_y - stem * (0.92 + 0.08 * ctx.contrast)
    inner_crown = min(inner_crown, crown_y - stem * 0.75)
    inner_crown = max(inner_crown, join_y + stem * 0.35)
    return NMetrics(
        stem=stem,
        counter=counter,
        x_height=ctx.x_height,
        ascender=ctx.ascender,
        overshoot=ctx.overshoot,
        crown_y=crown_y,
        leg_top=leg_top,
        join_y=join_y,
        kappa=kappa,
        inner_crown=inner_crown,
    )


@dataclass(frozen=True, slots=True)
class OMetrics:
    """Design record for the ``o`` family (``o b d p q``).

    The bowl is a superellipse ring centred at ``(rx, x_height / 2)``.
    ``thickness_v`` is the side (vertical) stroke; ``thickness_h`` is the
    top/bottom (horizontal) stroke — from ``stem`` and ``stem * contrast``.
    """

    rx: float
    ry: float
    thickness_v: float
    thickness_h: float
    exponent: float
    x_height: float
    overshoot: float

    @property
    def width(self) -> float:
        return 2.0 * self.rx

    @property
    def thickness(self) -> float:
        """Vertical stroke width (legacy alias for ``thickness_v``)."""
        return self.thickness_v

    def tuned(self, **kwargs: float) -> OMetrics:
        if "thickness" in kwargs:
            t = kwargs.pop("thickness")
            kwargs.setdefault("thickness_v", t)
            kwargs.setdefault("thickness_h", t)
        return replace(self, **kwargs)


def o_metrics(ctx: DesignContext) -> OMetrics:
    """Derive the ``o`` design record from family proportions."""
    ry = ctx.x_height / 2.0 + ctx.overshoot
    rx = ry * (0.88 + 0.10 * ctx.aperture)
    # Squircle when roundness low (coding); ellipse when soft.
    exponent = 2.0 + 0.7 * (1.0 - max(0.0, min(1.0, ctx.roundness)))
    return OMetrics(
        rx=rx,
        ry=ry,
        thickness_v=ctx.stem,
        thickness_h=ctx.stem * ctx.contrast * _horizontal_slant_scale(ctx),
        exponent=exponent,
        x_height=ctx.x_height,
        overshoot=ctx.overshoot,
    )


def _n_record(glyph: ComposedGlyph) -> NMetrics:
    return glyph.design if isinstance(glyph.design, NMetrics) else n_metrics(glyph.context)


def _o_record(glyph: ComposedGlyph) -> OMetrics:
    return glyph.design if isinstance(glyph.design, OMetrics) else o_metrics(glyph.context)


# --- shoulder geometry ------------------------------------------------------


@dataclass(frozen=True, slots=True)
class _Shoulder:
    """Named cubics of an ``n`` shoulder in ``n`` coordinates (left stem at x=0).

    ``outer`` runs left spring → crown → right leg top; ``inner`` runs right
    join → inner crown → left join. ``r`` and ``m`` reuse these curves.
    """

    outer: tuple[Cubic, Cubic]
    inner: tuple[Cubic, Cubic]
    l0: float
    l1: float
    r0: float
    r1: float


def _shoulder(m: NMetrics, x0: float = 0.0) -> _Shoulder:
    t, w, k = m.stem, m.counter, m.kappa
    l0, l1 = x0, x0 + t
    r0, r1 = x0 + t + w, x0 + t + w + t
    mid = (l1 + r0) / 2.0
    crown, leg_top, join, ic = m.crown_y, m.leg_top, m.join_y, m.inner_crown
    spring = m.x_height
    outer = (
        ((l1, spring), (l1, spring + k * (crown - spring)), (mid - k * (mid - l1), crown), (mid, crown)),
        ((mid, crown), (mid + k * (r1 - mid), crown), (r1, leg_top + k * (crown - leg_top)), (r1, leg_top)),
    )
    inner = (
        ((r0, join), (r0, join + k * (ic - join)), (mid + k * (r0 - mid), ic), (mid, ic)),
        ((mid, ic), (mid - k * (mid - l1), ic), (l1, join + k * (ic - join)), (l1, join)),
    )
    return _Shoulder(outer, inner, l0, l1, r0, r1)


def _curve(b: PathBuilder, c: Cubic) -> None:
    b.curveTo(c[1][0], c[1][1], c[2][0], c[2][1], c[3][0], c[3][1])


def _split(c: Cubic, where: float, *, horizontal: bool) -> tuple[Cubic, Cubic] | None:
    """Split ``c`` where it crosses ``x = where`` (or ``y`` if ``horizontal``)."""
    pieces = splitCubic(*c, where, horizontal)
    if len(pieces) != 2:
        return None
    a, b = pieces
    return (tuple(a), tuple(b))


def _ccw(outline: Outline) -> Outline:
    """Font convention: outer contour CCW (positive signed area)."""
    c0 = outline.contours[0]
    if signed_area(c0) < 0:
        return Outline((reverse_contour(c0),))
    return outline


def _mirror_cubic(cx: float, c: Cubic) -> Cubic:
    return (
        (2.0 * cx - c[0][0], c[0][1]),
        (2.0 * cx - c[1][0], c[1][1]),
        (2.0 * cx - c[2][0], c[2][1]),
        (2.0 * cx - c[3][0], c[3][1]),
    )


def _u_foot_bulge(c: DesignContext, stem: float) -> float:
    """Baseline toe fillet on low-roundness presets (TK-204)."""
    if c.roundness >= 0.35:
        return 0.0
    return max(stem * 0.08, 4.0)


def _u_foot_shelf(stem: float) -> float:
    return stem * 0.20


def _u_append_baseline_toe(
    b: PathBuilder, lo: float, li: float, bulge: float, shelf: float
) -> None:
    x_shelf = li - shelf
    if bulge <= 0.0:
        b.lineTo(li, 0.0)
        return
    b.curveTo(lo, -bulge, x_shelf - bulge * 0.5, 0.0, x_shelf, 0.0)
    b.lineTo(li, 0.0)


def _u_family_outline(m: NMetrics, ctx: DesignContext, *, vf_compat: bool = False) -> Outline:
    bulge = _u_foot_bulge(ctx, m.stem)
    if bulge <= 0.0:
        return _ccw(
            mirror_x(
                _n_family_outline(
                    m,
                    left_top=m.x_height,
                    vf_compat=vf_compat,
                    ctx=ctx,
                    shelf_left_foot=_stem_serif_inlined(ctx),
                ),
                at_x=m.width / 2.0,
            )
        )
    s = _shoulder(m)
    cx = m.width / 2.0
    ro, ri = 2.0 * cx - s.l0, 2.0 * cx - s.l1
    lo, li = 2.0 * cx - s.r1, 2.0 * cx - s.r0
    b = PathBuilder()
    b.moveTo(ro, 0.0)
    b.lineTo(ro, m.x_height)
    b.lineTo(ri, m.x_height)
    if vf_compat:
        b.lineTo(ri, m.x_height)
    _curve(b, _mirror_cubic(cx, s.outer[0]))
    _curve(b, _mirror_cubic(cx, s.outer[1]))
    b.lineTo(lo, 0.0)
    _u_append_baseline_toe(b, lo, li, bulge, _u_foot_shelf(m.stem))
    b.lineTo(li, m.join_y)
    _curve(b, _mirror_cubic(cx, s.inner[0]))
    _curve(b, _mirror_cubic(cx, s.inner[1]))
    b.lineTo(ri, 0.0)
    b.closePath()
    return _ccw(b.build())


def _u_branching_outline(m: NMetrics, ctx: DesignContext, *, stem_top: float) -> Outline:
    bulge = _u_foot_bulge(ctx, m.stem)
    if bulge <= 0.0:
        return _ccw(
            mirror_x(
                _n_branching_outline(
                    m,
                    stem_top=stem_top,
                    ctx=ctx,
                    shelf_left_foot=_stem_serif_inlined(ctx),
                ),
                at_x=m.width / 2.0,
            )
        )
    branch_y = _italic_branch_y(m, stem_top)
    drop = stem_top - branch_y
    mm = m.tuned(
        x_height=branch_y,
        crown_y=m.crown_y - drop * 0.14,
        leg_top=m.leg_top - drop * 0.2,
        join_y=min(m.join_y, branch_y - m.stem * 0.32),
        inner_crown=m.inner_crown - drop * 0.16,
    )
    s = _shoulder(mm)
    cx = m.width / 2.0
    ro, ri = 2.0 * cx - 0.0, 2.0 * cx - m.stem
    lo, li = 2.0 * cx - m.width, 2.0 * cx - (m.stem + m.counter)
    b = PathBuilder()
    b.moveTo(ro, 0.0)
    b.lineTo(ro, stem_top)
    b.lineTo(ri, stem_top)
    b.lineTo(ri, branch_y)
    _curve(b, _mirror_cubic(cx, s.outer[0]))
    _curve(b, _mirror_cubic(cx, s.outer[1]))
    b.lineTo(lo, 0.0)
    _u_append_baseline_toe(b, lo, li, bulge, _u_foot_shelf(m.stem))
    b.lineTo(li, mm.join_y)
    _curve(b, _mirror_cubic(cx, s.inner[0]))
    _curve(b, _mirror_cubic(cx, s.inner[1]))
    b.lineTo(ri, 0.0)
    b.closePath()
    return _ccw(b.build())


def _n_slab_left_foot_detour(
    b: PathBuilder,
    l0: float,
    l1: float,
    left_top: float,
    ctx: DesignContext,
    stem: float,
) -> None:
    """Slab foot below baseline; ends on ``(l0, left_top)``."""
    from typekernel.parts.caps import _finish_baseline_foot_pad
    from typekernel.parts.serifs import serif_metrics

    length, thick, _ = serif_metrics(ctx)
    l = min(length, stem * 0.5)
    th = min(thick, ctx.x_height * 0.1, stem * 0.2)
    _, _, bracket_r = serif_metrics(ctx)
    b.lineTo(l0 - l, -th)
    _finish_baseline_foot_pad(b, l0 - l, l1 + l, th, 0.0, bracketed=False)
    from typekernel.parts.serifs import _bracket_fillet_at_outer_corner

    _bracket_fillet_at_outer_corner(
        b,
        x_corner=l0,
        y_horiz=0.0,
        y_vert_end=left_top,
        x_from=l1 + l,
        bracket_r=bracket_r,
    )


def _n_bracketed_left_foot_detour(
    b: PathBuilder,
    l0: float,
    l1: float,
    left_top: float,
    ctx: DesignContext,
    stem: float,
) -> None:
    """Bracketed foot below baseline; ends on ``(l0, left_top)`` with a stem fillet."""
    from typekernel.parts.caps import _finish_baseline_foot_pad
    from typekernel.parts.serifs import (
        _bracket_fillet_at_outer_corner,
        bracketed_stem_foot_dims,
        serif_metrics,
    )

    l, th = bracketed_stem_foot_dims(ctx, stem, 0.0)
    _, _, bracket_r = serif_metrics(ctx)
    b.lineTo(l0 - l, -th)
    _finish_baseline_foot_pad(b, l0 - l, l1 + l, th, bracket_r, bracketed=True)
    _bracket_fillet_at_outer_corner(
        b,
        x_corner=l0,
        y_horiz=0.0,
        y_vert_end=left_top,
        x_from=l1 + l,
        bracket_r=bracket_r,
    )


def _n_left_stem_foot_detour(
    b: PathBuilder,
    l0: float,
    l1: float,
    left_top: float,
    ctx: DesignContext,
    stem: float,
) -> None:
    if ctx.style.serif == "bracketed":
        _n_bracketed_left_foot_detour(b, l0, l1, left_top, ctx, stem)
    else:
        _n_slab_left_foot_detour(b, l0, l1, left_top, ctx, stem)


def _n_begin_left_stem(
    b: PathBuilder,
    l0: float,
    l1: float,
    left_top: float,
    ctx: DesignContext,
    stem: float,
    *,
    shelf_foot: bool,
) -> None:
    """Rise on the left stem from the baseline, with optional inlined foot."""
    b.moveTo(l0, 0.0)
    if not _stem_serif_inlined(ctx):
        b.lineTo(l0, left_top)
        return
    if shelf_foot:
        from typekernel.parts.serifs import inline_stem_foot_serif_path

        inline_stem_foot_serif_path(b, l0, 0.0, ctx, stem)
        b.lineTo(l0, left_top)
        return
    _n_left_stem_foot_detour(b, l0, l1, left_top, ctx, stem)


def _n_inline_right_stem_foot(
    b: PathBuilder, x_stem_right: float, ctx: DesignContext, stem: float
) -> None:
    from typekernel.parts.serifs import inline_stem_foot_serif_path_right

    inline_stem_foot_serif_path_right(b, x_stem_right, 0.0, ctx, stem)


def _n_inline_left_stem_cap(
    b: PathBuilder,
    x_stem_left: float,
    x_stem_right: float,
    y_cap: float,
    ctx: DesignContext,
    stem: float,
    *,
    slab_rect: bool = False,
    slab_rect_thickness_scale: float = 1.0,
) -> None:
    if not _stem_serif_inlined(ctx):
        return
    from typekernel.parts.serifs import (
        inline_stem_cap_serif_path,
        inline_stem_cap_serif_path_slab_rect,
    )

    if slab_rect:
        inline_stem_cap_serif_path_slab_rect(
            b,
            x_stem_left,
            x_stem_right,
            y_cap,
            ctx,
            stem,
            thickness_scale=slab_rect_thickness_scale,
        )
    else:
        inline_stem_cap_serif_path(b, x_stem_left, x_stem_right, y_cap, ctx, stem)


def _n_inline_shoulder_left_cap_slab(
    b: PathBuilder,
    x_stem_left: float,
    y_cap: float,
    ctx: DesignContext,
    stem: float,
) -> None:
    if ctx.style.serif not in ("slab", "bracketed"):
        return
    from typekernel.parts.serifs import inline_shoulder_left_cap_slab_path

    inline_shoulder_left_cap_slab_path(b, x_stem_left, y_cap, ctx, stem)


def _n_ascender_left_stem_cap(y_cap: float, m: NMetrics) -> bool:
    return y_cap > m.x_height + 0.5


def _n_slab_inlined(ctx: DesignContext | None) -> bool:
    return (
        ctx is not None
        and ctx.style.serif == "slab"
        and _stem_serif_inlined(ctx)
    )


def _n_bracketed_h_inlined(
    ctx: DesignContext | None, left_top: float, m: NMetrics
) -> bool:
    """Bracketed ``h``: slab-rect stem caps avoid R3 on ascender + right leg."""
    return (
        ctx is not None
        and ctx.style.serif == "bracketed"
        and _stem_serif_inlined(ctx)
        and left_top > m.x_height + 0.5
    )


def _n_bracketed_h_ascender_cap_thickness_scale(m: NMetrics) -> float:
    """Heavy ladder stems: thinner ascender cap preserves ``h`` counter pinch (R8)."""
    return 0.35 if m.stem <= 110.0 else 1.0


def _n_right_leg_top_cap_inlined(
    ctx: DesignContext | None, left_top: float, m: NMetrics
) -> bool:
    """Slab ``n``/``h`` and bracketed ``h``: inline right-leg top serif."""
    return _n_slab_inlined(ctx) or _n_bracketed_h_inlined(ctx, left_top, m)


def _n_slab_n_left_shoulder_cap(
    ctx: DesignContext | None, left_top: float, m: NMetrics
) -> bool:
    """Slab ``n``: full-width left stem cap at ``x_height`` (``stem_L_t``)."""
    return _n_slab_inlined(ctx) and abs(left_top - m.x_height) < 0.5


def _n_bracketed_n_left_shoulder_cap(
    ctx: DesignContext | None, left_top: float, m: NMetrics
) -> bool:
    """Bracketed ``n``: left-face shoulder cap at ``x_height`` (``stem_L_t``)."""
    return (
        ctx is not None
        and ctx.style.serif == "bracketed"
        and _stem_serif_inlined(ctx)
        and abs(left_top - m.x_height) < 0.5
    )


def _n_family_outline(
    m: NMetrics,
    *,
    left_top: float,
    vf_compat: bool = False,
    ctx: DesignContext | None = None,
    shelf_left_foot: bool = False,
) -> Outline:
    """One continuous outer contour: left stem + shoulder + right leg.

    No third ``arch`` mesh and no ``union``. The counter is the notch formed
    by the stem insides and the inner shoulder.
    """
    s = _shoulder(m)
    b = PathBuilder()
    if ctx is not None:
        _n_begin_left_stem(
            b, s.l0, s.l1, left_top, ctx, m.stem, shelf_foot=shelf_left_foot
        )
        if _n_bracketed_n_left_shoulder_cap(ctx, left_top, m):
            _n_inline_shoulder_left_cap_slab(b, s.l0, left_top, ctx, m.stem)
        b.lineTo(s.l1, left_top)
        if _n_ascender_left_stem_cap(left_top, m):
            bracket_h = _n_bracketed_h_inlined(ctx, left_top, m)
            _n_inline_left_stem_cap(
                b,
                s.l0,
                s.l1,
                left_top,
                ctx,
                m.stem,
                slab_rect=bracket_h,
                slab_rect_thickness_scale=(
                    _n_bracketed_h_ascender_cap_thickness_scale(m) if bracket_h else 1.0
                ),
            )
    else:
        b.moveTo(s.l0, 0.0)
        b.lineTo(s.l0, left_top)
        b.lineTo(s.l1, left_top)
    if left_top > m.x_height + 0.5:
        # h: down the right face of the ascender stem to the shoulder spring
        b.lineTo(s.l1, m.x_height)
    elif vf_compat:
        b.lineTo(s.l1, left_top)
    if _n_slab_n_left_shoulder_cap(ctx, left_top, m):
        slab_ctx = ctx
        assert slab_ctx is not None
        _n_inline_left_stem_cap(b, s.l0, s.l1, m.x_height, slab_ctx, m.stem)
    _curve(b, s.outer[0])
    if _n_right_leg_top_cap_inlined(ctx, left_top, m):
        cap_ctx = ctx
        assert cap_ctx is not None
        split_outer = _split(s.outer[1], m.x_height, horizontal=True)
        if split_outer is not None:
            _curve(b, split_outer[0])
            b.lineTo(s.r1, m.x_height)
            _n_inline_left_stem_cap(
                b,
                s.r0,
                s.r1,
                m.x_height,
                cap_ctx,
                m.stem,
                slab_rect=_n_bracketed_h_inlined(ctx, left_top, m),
            )
            b.lineTo(s.r1, split_outer[1][3][1])
        else:
            _curve(b, s.outer[1])
    else:
        _curve(b, s.outer[1])
    b.lineTo(s.r1, 0.0)
    if ctx is not None and _stem_serif_inlined(ctx):
        _n_inline_right_stem_foot(b, s.r1, ctx, m.stem)
    b.lineTo(s.r0, 0.0)
    b.lineTo(s.r0, m.join_y)
    _curve(b, s.inner[0])
    _curve(b, s.inner[1])
    b.lineTo(s.l1, 0.0)
    b.closePath()
    return _ccw(b.build())


def _pack(
    ctx: DesignContext,
    record: object,
    anchors: dict[str, Pt],
    *outlines: Outline,
) -> ComposedGlyph:
    """Sidebearing pack; single outline — no boolean letter topology."""
    asm = GlyphAssembler(ctx).with_design(record)
    for o in outlines:
        asm.add(_ccw(o))
    for name, (x, y) in anchors.items():
        asm.anchor(name, x, y)
    return asm.build()


# --- n family -----------------------------------------------------------------


def _italic_topology(ctx: DesignContext) -> bool:
    """True when construct slant should use branching arches (M4 TK-403)."""
    return ctx.italic_slant_deg >= 6.0 or bool(ctx.vf_compat_oblique_splits)


def _vf_compat_stem(ctx: DesignContext) -> bool:
    return bool(ctx.vf_compat_stem_segments)


def _stem_serif_inlined(ctx: DesignContext) -> bool:
    """Slab/bracketed feet drawn in the stem outline (not anchor boolean)."""
    return ctx.style.serif in ("slab", "bracketed")


def _inline_single_stem_outline(ctx: DesignContext, stem: float, top: float) -> Outline:
    """Vertical stem with inlined foot/cap serifs (``i``/``l``/cap ``I`` recipe)."""
    from typekernel.parts.caps import (
        HMetrics,
        _i_slab_outline_points,
        _polygon,
        _write_i_bracketed_outer,
    )

    h = HMetrics(
        stem=stem,
        bar=stem * ctx.contrast * 0.92,
        cap_height=top,
        width=stem,
        bar_y=top * 0.52,
        overshoot=0.0,
    )
    if ctx.style.serif == "slab":
        return _polygon(_i_slab_outline_points(h, ctx))
    b = PathBuilder()
    _write_i_bracketed_outer(b, h, ctx)
    return _ccw(b.build())


def _f_stem_floor(ctx: DesignContext) -> float:
    if _italic_topology(ctx):
        return ctx.descender * 0.78
    return 0.0


def _hook_slab_stem_foot(ctx: DesignContext, stem: float) -> tuple[float, float, float] | None:
    """Inline cap serif on hook letters (slab + bracketed), or ``None``.

    Returns ``(length, thickness, bracket_radius)``; ``bracket_radius`` is zero for slab.
    """
    if ctx.style.serif not in ("slab", "bracketed"):
        return None
    from typekernel.parts.serifs import serif_metrics

    length, thick, bracket_r = serif_metrics(ctx)
    xh = ctx.x_height
    if ctx.style.serif == "bracketed":
        from typekernel.parts.serifs import bracketed_stem_foot_dims

        l, th = bracketed_stem_foot_dims(ctx, stem, 0.0)
    else:
        l = min(length * 0.42, stem * 0.48)
        th = min(thick * 0.65, xh * 0.05, stem * 0.18)
        bracket_r = 0.0
    return l, th, bracket_r


def _f_use_inline_crossbar(ctx: DesignContext) -> bool:
    return _italic_topology(ctx) or _vf_compat_stem(ctx)


def _horizontal_slant_scale(ctx: DesignContext) -> float:
    from typekernel.parts.slant_compensate import horizontal_slant_compensation

    return horizontal_slant_compensation(ctx)


def _e_oblique_shear(ctx: DesignContext) -> float | None:
    """Shear used to pre-split ``e`` before construct slant (TK-402)."""
    if abs(ctx.italic_slant_deg) >= 6.0:
        return math.tan(math.radians(ctx.italic_slant_deg))
    if ctx.vf_compat_oblique_splits:
        return math.tan(math.radians(ctx.vf_oblique_split_deg))
    return None


def _italic_branch_y(m: NMetrics, stem_top: float) -> float:
    if stem_top > m.x_height + 1.0:
        return m.x_height + (stem_top - m.x_height) * 0.38
    return m.x_height * 0.5


def _n_branching_outline(
    m: NMetrics,
    *,
    stem_top: float,
    ctx: DesignContext | None = None,
    shelf_left_foot: bool = False,
) -> Outline:
    """``n`` / ``h`` shoulder springing from the left stem mid-height (italic)."""
    branch_y = _italic_branch_y(m, stem_top)
    drop = stem_top - branch_y
    mm = m.tuned(
        x_height=branch_y,
        crown_y=m.crown_y - drop * 0.14,
        leg_top=m.leg_top - drop * 0.2,
        join_y=min(m.join_y, branch_y - m.stem * 0.32),
        inner_crown=m.inner_crown - drop * 0.16,
    )
    s = _shoulder(mm)
    t = m.stem
    l0, l1, r0, r1 = 0.0, t, t + m.counter, m.width
    b = PathBuilder()
    if ctx is not None:
        _n_begin_left_stem(
            b, l0, l1, stem_top, ctx, m.stem, shelf_foot=shelf_left_foot
        )
        b.lineTo(l1, stem_top)
        if _n_ascender_left_stem_cap(stem_top, m):
            _n_inline_left_stem_cap(b, l0, l1, stem_top, ctx, m.stem)
    else:
        b.moveTo(l0, 0.0)
        b.lineTo(l0, stem_top)
        b.lineTo(l1, stem_top)
    b.lineTo(l1, branch_y)
    _curve(b, s.outer[0])
    _curve(b, s.outer[1])
    b.lineTo(r1, 0.0)
    if ctx is not None and _stem_serif_inlined(ctx):
        _n_inline_right_stem_foot(b, r1, ctx, m.stem)
    b.lineTo(r0, 0.0)
    b.lineTo(r0, mm.join_y)
    _curve(b, s.inner[0])
    _curve(b, s.inner[1])
    b.lineTo(l1, 0.0)
    b.closePath()
    return _ccw(b.build())


def _n_stem_serif_anchors(
    m: NMetrics,
    *,
    left_top: float,
    right_top: float | None = None,
    left_foot: bool = True,
    right_foot: bool = True,
    left_cap: bool = True,
    ctx: DesignContext | None = None,
    inline_left_foot: bool = False,
    inline_right_foot: bool = False,
    inline_left_top: bool = False,
    inline_right_top: bool = False,
) -> dict[str, Pt]:
    """Stem feet/caps for ``n``-family letters (TK-306)."""
    half = m.stem / 2.0
    anchors: dict[str, Pt] = {}
    if left_foot and not (
        inline_left_foot and ctx is not None and _stem_serif_inlined(ctx)
    ):
        anchors["stem_L_b"] = (half, 0.0)
    if left_cap and not (
        inline_left_top and ctx is not None and _stem_serif_inlined(ctx)
    ):
        anchors["stem_L_t"] = (half, left_top)
    if right_foot and not (
        inline_right_foot and ctx is not None and _stem_serif_inlined(ctx)
    ):
        anchors["stem_R_b"] = (m.width - half, 0.0)
    if right_top is not None and not (
        inline_right_top and ctx is not None and _stem_serif_inlined(ctx)
    ):
        anchors["stem_R_t"] = (m.width - half, right_top)
    return anchors


def _vertical_stem_serif_anchors(
    stem: float,
    center_x: float,
    *,
    bottom: float,
    top: float,
    side: Literal["L", "R"] = "L",
    include_top: bool = True,
) -> dict[str, Pt]:
    """Single vertical stem feet/caps (``l``, ``f``, bowl stems, …)."""
    anchors: dict[str, Pt] = {f"stem_{side}_b": (center_x, bottom)}
    if include_top:
        anchors[f"stem_{side}_t"] = (center_x, top)
    return anchors


def build_n(ctx: DesignContext, metrics: NMetrics | None = None) -> ComposedGlyph:
    """Control ``n``: continuous cubic outline from its design record."""
    m = metrics or n_metrics(ctx)
    cx = m.width / 2.0
    anchors = {
        "top": (cx, m.x_height),
        "bottom": (cx, 0.0),
        **_n_stem_serif_anchors(
            m,
            left_top=m.x_height,
            right_top=None,
            ctx=ctx,
            inline_left_foot=_stem_serif_inlined(ctx),
            inline_right_foot=_stem_serif_inlined(ctx),
            inline_left_top=ctx.style.serif in ("slab", "bracketed"),
        ),
    }
    shelf_n = ctx.style.serif in ("slab", "bracketed")
    if _italic_topology(ctx):
        outline = _n_branching_outline(
            m, stem_top=m.x_height, ctx=ctx, shelf_left_foot=shelf_n
        )
    else:
        outline = _n_family_outline(
            m,
            left_top=m.x_height,
            vf_compat=_vf_compat_stem(ctx),
            ctx=ctx,
            shelf_left_foot=shelf_n,
        )
    return _pack(ctx, m, anchors, outline)


def build_h(ctx: DesignContext, metrics: NMetrics | None = None) -> ComposedGlyph:
    """``h`` from the same shoulder/leg recipe as ``n`` (ascender left stem)."""
    m = metrics or n_metrics(ctx)
    anchors = {
        "top": (m.stem / 2.0, m.ascender),
        "bottom": (m.width / 2.0, 0.0),
        **_n_stem_serif_anchors(
            m,
            left_top=m.ascender,
            right_top=m.x_height,
            ctx=ctx,
            inline_left_foot=_stem_serif_inlined(ctx),
            inline_right_foot=_stem_serif_inlined(ctx),
            inline_left_top=_stem_serif_inlined(ctx),
            inline_right_top=ctx.style.serif in ("slab", "bracketed"),
        ),
    }
    shelf_h = ctx.style.serif in ("slab", "bracketed")
    if _italic_topology(ctx):
        outline = _n_branching_outline(
            m, stem_top=m.ascender, ctx=ctx, shelf_left_foot=shelf_h
        )
    else:
        outline = _n_family_outline(
            m,
            left_top=m.ascender,
            vf_compat=_vf_compat_stem(ctx),
            ctx=ctx,
            shelf_left_foot=shelf_h,
        )
    return _pack(ctx, m, anchors, outline)


def h_from_n(n_glyph: ComposedGlyph, ctx: DesignContext | None = None) -> ComposedGlyph:
    """Derive ``h`` from control ``n``: same shoulder and leg, ascending stem.

    Reads the ``n`` design record carried on ``n_glyph``, so a tuned ``n``
    yields a matching ``h``.
    """
    return build_h(ctx or n_glyph.context, _n_record(n_glyph))


def r_from_n(
    n_glyph: ComposedGlyph,
    ctx: DesignContext | None = None,
    *,
    arm: float = 0.5,
) -> ComposedGlyph:
    """Derive ``r``: the ``n`` stem and shoulder, cut off at a vertical terminal.

    ``arm`` places the terminal between the counter's centre (``0``) and the
    right leg's inner face (``1``). Outer and inner shoulder curves are split
    at that x, so the arm is literally the ``n`` shoulder, truncated.
    """
    c = ctx or n_glyph.context
    m = _n_record(n_glyph)
    scaled = arm * r_arm_scale(c)
    if _italic_topology(c):
        outline, x_t = _r_branching_outline(m, scaled, c)
    else:
        outline, x_t = _r_outline(m, scaled, vf_compat=_vf_compat_stem(c), ctx=c)
    outline = apply_terminal_shear(c, outline)
    anchors = {
        "top": (x_t / 2.0, m.x_height),
        "bottom": (m.stem / 2.0, 0.0),
        **_n_stem_serif_anchors(
            m,
            left_top=m.x_height,
            right_foot=False,
            ctx=c,
            inline_left_foot=_stem_serif_inlined(c),
            inline_left_top=c.style.serif in ("slab", "bracketed"),
        ),
    }
    return _pack(c, m, anchors, outline)


def _r_pieces(m: NMetrics, arm: float) -> tuple[_Shoulder, Cubic, Cubic, float]:
    """The ``n`` shoulder cut at the ``r`` terminal.

    Returns ``(shoulder, outer_arm, inner_arm, x_t)``: ``outer_arm`` runs from
    the crown to the terminal, ``inner_arm`` from the terminal to the inner
    crown.
    """
    if not 0.0 < arm < 1.0:
        raise ValueError(f"arm must be in (0, 1), got {arm}")
    s = _shoulder(m)
    mid = s.outer[0][3][0]
    x_t = mid + arm * (s.r0 - mid)
    outer = _split(s.outer[1], x_t, horizontal=False)
    inner = _split(s.inner[0], x_t, horizontal=False)
    if outer is None or inner is None:  # pragma: no cover - monotonic by construction
        raise ValueError("shoulder does not cross the terminal position")
    return s, outer[0], inner[1], x_t


Bar = tuple[float, float, float, float]
"""``(y0, y1, left, right)``: a crossbar from ``y0`` to ``y1`` reaching
``left`` past the stem's left face and ``right`` past its right face."""


def _r_outline(
    m: NMetrics,
    arm: float,
    bar: Bar | None = None,
    *,
    vf_compat: bool = False,
    stem_floor: float = 0.0,
    hook_stem_knots: bool = False,
    hook_belly: float = 0.0,
    slab_foot: tuple[float, float, float] | None = None,
    ctx: DesignContext | None = None,
) -> tuple[Outline, float]:
    """``r``-type outline (stem + truncated shoulder) and its terminal x.

    ``bar`` adds a crossbar as straight detours on both stem faces, so the
    contour keeps one fixed point count (no boolean union).
    """
    s, outer_arm, inner_arm, x_t = _r_pieces(m, arm)
    if bar is not None and not 0.0 < bar[0] < bar[1] < m.join_y:
        raise ValueError("crossbar must sit between the baseline and the shoulder crotch")

    b = PathBuilder()
    b.moveTo(s.l0, stem_floor if hook_stem_knots else 0.0)
    if hook_stem_knots or vf_compat:
        b.lineTo(s.l0, 0.0)
    if bar is not None:
        y0, y1, left, _ = bar
        for p in ((s.l0, y0), (s.l0 - left, y0), (s.l0 - left, y1), (s.l0, y1)):
            b.lineTo(*p)
        if hook_stem_knots:
            b.lineTo(s.l1, y1)
    if (
        ctx is not None
        and _stem_serif_inlined(ctx)
        and not hook_stem_knots
        and bar is None
        and abs(stem_floor) < 1e-6
    ):
        from typekernel.parts.serifs import inline_stem_foot_serif_path

        inline_stem_foot_serif_path(b, s.l0, 0.0, ctx, m.stem)
        b.lineTo(s.l0, m.x_height)
        _n_inline_shoulder_left_cap_slab(b, s.l0, m.x_height, ctx, m.stem)
    else:
        b.lineTo(s.l0, m.x_height)
    if slab_foot is not None:
        foot_l, foot_th, foot_br = slab_foot
        base_y = m.x_height
        if foot_br > 0.0:
            from typekernel.parts.serifs import inline_hook_cap_serif_path

            inline_hook_cap_serif_path(b, s.l0, s.l1, base_y, foot_l, foot_th, foot_br)
        else:
            b.lineTo(s.l0 - foot_l, base_y)
            b.lineTo(s.l0 - foot_l, base_y + foot_th)
            b.lineTo(s.l1, base_y + foot_th)
            b.lineTo(s.l1, base_y)
    b.lineTo(s.l1, m.x_height)
    if vf_compat:
        b.lineTo(s.l1, m.x_height)
    _curve(b, s.outer[0])
    _curve(b, outer_arm)
    if hook_belly > 0.0:
        p_here = outer_arm[3]
        p_out = inner_arm[0]
        b.curveTo(
            p_here[0] - hook_belly * 0.55,
            p_here[1] - hook_belly * 0.4,
            p_out[0],
            p_out[1] + hook_belly * 0.2,
            p_out[0],
            p_out[1],
        )
    else:
        b.lineTo(*inner_arm[0])
    _curve(b, inner_arm)
    _curve(b, s.inner[1])
    if bar is not None:
        y0, y1, _, right = bar
        for p in ((s.l1, y1), (s.l1 + right, y1), (s.l1 + right, y0), (s.l1, y0)):
            b.lineTo(*p)
    b.lineTo(s.l1, 0.0)
    if hook_stem_knots:
        b.lineTo(s.l0, 0.0)
        if abs(stem_floor) < 1e-6:
            b.lineTo(s.l0, 0.0)
    b.closePath()
    return _ccw(b.build()), x_t


def _r_branching_outline(
    m: NMetrics, arm: float, ctx: DesignContext
) -> tuple[Outline, float]:
    """Italic ``r``: branching shoulder truncated at the terminal."""
    branch_y = _italic_branch_y(m, m.x_height)
    drop = m.x_height - branch_y
    mm = m.tuned(
        x_height=branch_y,
        crown_y=m.crown_y - drop * 0.14,
        leg_top=m.leg_top - drop * 0.2,
        join_y=min(m.join_y, branch_y - m.stem * 0.32),
        inner_crown=m.inner_crown - drop * 0.16,
    )
    s, outer_arm, inner_arm, x_t = _r_pieces(mm, arm)
    b = PathBuilder()
    b.moveTo(s.l0, 0.0)
    if _stem_serif_inlined(ctx):
        from typekernel.parts.serifs import inline_stem_foot_serif_path

        inline_stem_foot_serif_path(b, s.l0, 0.0, ctx, m.stem)
    b.lineTo(s.l0, m.x_height)
    b.lineTo(s.l1, m.x_height)
    b.lineTo(s.l1, branch_y)
    b.lineTo(s.l1, branch_y)
    _curve(b, s.outer[0])
    _curve(b, outer_arm)
    b.lineTo(*inner_arm[0])
    _curve(b, inner_arm)
    _curve(b, s.inner[1])
    b.lineTo(s.l1, 0.0)
    b.closePath()
    return _ccw(b.build()), x_t


def _hook_shoulder_rise(ctx: DesignContext, m: NMetrics) -> float:
    """How far the hook crown sits above the stem flat (more than ``overshoot``).

    ``n``/``h`` keep ``crown_y = x_height + overshoot``; hooks need a taller
    shoulder so ``f t j g r`` arcs do not read as an ``L`` at low roundness.
    """
    return max(ctx.overshoot * 1.35, m.stem * (0.26 + 0.20 * ctx.roundness))


def _hook_shoulder_kappa(ctx: DesignContext, m: NMetrics) -> float:
    """Slightly rounder shoulder handles on hooks than on the ``n`` control."""
    return m.kappa * (1.05 + 0.32 * ctx.roundness)


def _hook_record(
    m: NMetrics,
    top: float,
    ctx: DesignContext,
    depth: float = 0.45,
) -> NMetrics:
    """The ``n`` record re-based so its shoulder caps a stem of height ``top``.

    Crown uses :func:`_hook_shoulder_rise` instead of shifting the ``n`` crown
    by ``top - x_height`` (which left only ``overshoot`` above ``f``/``t``).
    The crotch is ``depth`` × as deep as the ``n``'s, since hooks sit tighter.
    """
    rise = _hook_shoulder_rise(ctx, m)
    crown = top + rise
    shoulder_thickness = m.crown_y - m.inner_crown
    inner_crown = max(crown - shoulder_thickness, top + m.stem * 0.22)
    join = min(top - depth * (m.x_height - m.join_y), inner_crown - 0.35 * m.stem)
    leg_top = top - m.stem * 0.02
    return m.tuned(
        x_height=top,
        crown_y=crown,
        leg_top=leg_top,
        join_y=join,
        inner_crown=inner_crown,
        kappa=_hook_shoulder_kappa(ctx, m),
    )


def _finish_hook_letter(outline: Outline, ctx: DesignContext) -> Outline:
    """Blend kinks on hook letters (``f`` ``t`` ``j``) after the fixed contour."""
    from typekernel.geo.joins import blend_corners, default_selector

    radius = max(3.0, ctx.join_radius * 1.15)
    return blend_corners(outline, radius, select=default_selector, tension=1.0)


def _crossbar_counter(m: NMetrics, ctx: DesignContext) -> float:
    """Stem-relief counter widening without over-wide ``f``/``t`` crossbar detours."""
    from typekernel.parts.weight_relief import stem_weight_fraction

    t = stem_weight_fraction(m.stem)
    if t <= 0.68:
        return m.counter
    base = n_metrics(ctx).counter
    pull = min(1.0, (t - 0.68) / 0.32)
    coef = 0.78 + 0.15 * min(1.0, max(0.0, (t - 0.75) / 0.25))
    return m.counter + pull * coef * (base - m.counter)


def _crossbar(c: DesignContext, m: NMetrics, hook: NMetrics, x_height: float) -> Bar:
    """Bar at x-height (dropped just enough to clear a heavy hook's crotch)."""
    tb = m.stem * c.contrast * 0.95 * _horizontal_slant_scale(c)
    y1 = min(x_height, hook.join_y - 0.1 * m.stem)
    ctr = _crossbar_counter(m, c)
    return (y1 - tb, y1, 0.42 * ctr, 0.52 * ctr)


def _t_crossbar_in_hook_space(c: DesignContext, m: NMetrics, hook: NMetrics, top: float) -> Bar:
    """Crossbar in hook coordinates before ``t`` is flipped."""
    from typekernel.parts.weight_relief import stem_weight_fraction

    tb = m.stem * c.contrast * 0.95 * _horizontal_slant_scale(c)
    y0 = top - m.x_height
    ctr = _crossbar_counter(m, c)
    t = stem_weight_fraction(m.stem)
    if t > 0.78 and c.roundness >= 0.35:
        base = n_metrics(c).counter
        blend = min(1.0, (t - 0.78) / 0.22) * 0.62
        ctr = ctr + blend * (base - ctr)
    return (y0, y0 + tb, 0.42 * ctr, 0.52 * ctr)


def _hook_with_crossbar_outline(
    hook: NMetrics,
    n_m: NMetrics,
    ctx: DesignContext,
    arm: float,
    bar: Bar,
    *,
    blend: bool = True,
    inline_crossbar: bool = False,
    hook_belly: float = 0.0,
    slab_foot: tuple[float, float, float] | None = None,
) -> tuple[Outline, float]:
    """Hook master + crossbar as fixed stem detours (no boolean union)."""
    del n_m
    outline, x_t = _r_outline(
        hook,
        arm,
        bar,
        vf_compat=inline_crossbar,
        stem_floor=_f_stem_floor(ctx) if inline_crossbar else 0.0,
        hook_stem_knots=inline_crossbar,
        hook_belly=hook_belly,
        slab_foot=slab_foot,
    )
    if blend and not inline_crossbar:
        outline = _finish_hook_letter(outline, ctx)
    return outline, x_t


def f_from_n(
    n_glyph: ComposedGlyph,
    ctx: DesignContext | None = None,
    *,
    arm: float = 0.75,
) -> ComposedGlyph:
    """Derive ``f``: the ``r`` arm capping an ascender stem, crossbar at x-height."""
    c = ctx or n_glyph.context
    m = _n_record(n_glyph)
    hook = _hook_record(m, m.ascender, c)
    bar = _crossbar(c, m, hook, m.x_height)
    inline = _f_use_inline_crossbar(c)
    outline, _ = _hook_with_crossbar_outline(
        hook,
        m,
        c,
        arm,
        bar,
        blend=not inline,
        inline_crossbar=inline,
        slab_foot=_hook_slab_stem_foot(c, m.stem),
    )
    outline = apply_terminal_shear(c, outline)
    half = m.stem / 2.0
    anchors: dict[str, Pt] = {"bottom": (half, 0.0)}
    if c.style.serif not in ("slab", "bracketed"):
        anchors.update(
            _vertical_stem_serif_anchors(
                m.stem, half, bottom=0.0, top=m.ascender, side="L", include_top=False
            )
        )
    return _pack(c, m, anchors, outline)


def t_from_n(
    n_glyph: ComposedGlyph,
    ctx: DesignContext | None = None,
    *,
    arm: float = 0.6,
    rise: float = 0.3,
) -> ComposedGlyph:
    """Derive ``t``: the ``f`` construction flipped, hook on the baseline.

    The stem stands ``rise`` of the way from x-height to the ascender; the
    hook dips below the baseline by the overshoot.
    """
    c = ctx or n_glyph.context
    m = _n_record(n_glyph)
    top = m.x_height + rise * (m.ascender - m.x_height)
    from typekernel.parts.weight_relief import stem_weight_fraction

    t_w = stem_weight_fraction(m.stem)
    hook_depth = 0.45
    if 0.24 <= c.roundness < 0.32 and t_w > 0.75:
        hook_depth = 0.45 - 0.1 * min(1.0, (t_w - 0.75) / 0.25)
    hook = _hook_record(m, top, c, depth=hook_depth)
    # Built upside down (hook on top), then flipped: the bar [xh - tb, xh]
    # sits at [top - xh, top - xh + tb] before the flip.
    bar = _t_crossbar_in_hook_space(c, m, hook, top)
    belly_scale = 0.06 + 0.94 * min(1.0, max(0.0, (t_w - 0.68) / 0.32))
    belly = _hook_belly_fillet(m.stem) * belly_scale
    outline, _x_t = _hook_with_crossbar_outline(
        hook,
        m,
        c,
        arm,
        bar,
        blend=False,
        hook_belly=belly,
        slab_foot=_hook_slab_stem_foot(c, m.stem),
    )
    flipped = _ccw(mirror_y(outline, at_y=top / 2.0))
    try:
        _, min_y, max_x, _ = bounds(flipped)
    except ValueError:
        min_y, max_x = 0.0, m.stem
    tip = (max_x, min_y + m.stem * 0.12)
    if c.style.t_cut == "slanted":
        from typekernel.parts.terminals import shear_end

        band = max(6.0, c.stem * 0.38)
        outline = shear_end(flipped, tip, -16.0, band=band, along="y", inward="-")
    else:
        outline = apply_terminal_shear(c, flipped, at=tip)
    half = m.stem / 2.0
    anchors: dict[str, Pt] = {"bottom": (half, 0.0)}
    if c.style.serif not in ("slab", "bracketed"):
        anchors.update(
            _vertical_stem_serif_anchors(
                m.stem, half, bottom=0.0, top=top, side="L", include_top=False
            )
        )
    return _pack(c, m, anchors, outline)


def j_from_n(
    n_glyph: ComposedGlyph,
    ctx: DesignContext | None = None,
    *,
    arm: float = 0.75,
) -> ComposedGlyph:
    """Derive ``j``: the ``r`` turned 180° into a descender hook, plus the ``i`` tittle."""
    c = ctx or n_glyph.context
    m = _n_record(n_glyph)
    height = m.x_height - c.descender
    hook = _hook_record(m, height, c)
    outline, _ = _r_outline(
        hook,
        arm,
        hook_belly=_hook_belly_fillet(m.stem),
        slab_foot=_hook_slab_stem_foot(c, m.stem),
    )
    turned = mirror_y(mirror_x(outline, at_x=m.stem / 2.0), at_y=height / 2.0)
    body = translate(turned, 0.0, c.descender)
    tip = (m.stem * 1.05, c.descender + m.stem * 0.28)
    body = apply_terminal_shear(c, body, at=tip)
    dot_y = m.x_height + m.stem * 0.55
    dot = tittle(c, m.stem / 2.0, dot_y, size=m.stem * 0.95)
    half = m.stem / 2.0
    anchors: dict[str, Pt] = {
        "top": (half, dot_y + m.stem * 0.95),
        "bottom": (half, c.descender),
    }
    if c.style.serif not in ("slab", "bracketed"):
        anchors.update(
            _vertical_stem_serif_anchors(
                m.stem,
                half,
                bottom=c.descender,
                top=m.x_height,
                side="L",
                include_top=False,
            )
        )
    return _pack(c, m, anchors, body, dot)


def build_r(ctx: DesignContext, metrics: NMetrics | None = None) -> ComposedGlyph:
    return r_from_n(build_n(ctx, metrics), ctx)


def m_from_n(
    n_glyph: ComposedGlyph,
    ctx: DesignContext | None = None,
    *,
    counter_scale: float | None = None,
) -> ComposedGlyph:
    """Derive ``m``: two ``n`` shoulders sharing the middle stem.

    Each counter is ``counter_scale`` of the ``n`` counter (designers narrow
    ``m`` so its colour matches ``n``). The first arch is cut where it comes
    down to the middle stem's top, which forms the crotch; one continuous
    contour, no boolean union.
    """
    c = ctx or n_glyph.context
    from typekernel.parts.weight_relief import m_counter_scale

    scale = counter_scale if counter_scale is not None else m_counter_scale(c.stem)
    if scale <= 0:
        raise ValueError(f"counter_scale must be positive, got {scale}")
    m = _n_record(n_glyph)
    # Slightly shallower shoulders than ``n`` so the double arch stays inside R9.
    mm = m.tuned(
        counter=m.counter * scale,
        # Shallower inner shoulder than ``n`` so the double-arch crotch stays open (TK-204).
        inner_crown=min(
            m.crown_y - m.stem * 0.55,
            m.inner_crown + 0.32 * m.stem,
        ),
    )
    xh = mm.x_height
    # Lift inner crown to x-height when needed so inner shoulders can meet the crotch shelf.
    mm = mm.tuned(
        inner_crown=min(
            max(mm.inner_crown, xh),
            mm.crown_y - mm.stem * 0.06,
        ),
    )
    branch_y: float | None = None
    if _italic_topology(c):
        branch_y = _italic_branch_y(m, xh)
        drop = xh - branch_y
        mm = mm.tuned(
            x_height=branch_y,
            crown_y=mm.crown_y - drop * 0.14,
            leg_top=mm.leg_top - drop * 0.2,
            join_y=min(mm.join_y, branch_y - mm.stem * 0.32),
            inner_crown=mm.inner_crown - drop * 0.16,
        )
    s1 = _shoulder(mm)
    s2 = _shoulder(mm, s1.r0)

    b = PathBuilder()
    b.moveTo(s1.l0, 0.0)
    if _stem_serif_inlined(c):
        from typekernel.parts.serifs import inline_stem_foot_serif_path

        inline_stem_foot_serif_path(b, s1.l0, 0.0, c, mm.stem)
        b.lineTo(s1.l0, xh)
        _n_inline_shoulder_left_cap_slab(b, s1.l0, xh, c, mm.stem)
    else:
        b.lineTo(s1.l0, xh)
    b.lineTo(s1.l1, xh)
    if branch_y is not None:
        b.lineTo(s1.l1, branch_y)
    elif _vf_compat_stem(c):
        b.lineTo(s1.l1, xh)
    _curve(b, s1.outer[0])
    split1 = _split(s1.outer[1], xh, horizontal=True)
    split2 = _split(s2.outer[0], xh, horizontal=True)
    if split1 is not None and split2 is not None:
        _curve(b, split1[0])
        _curve(b, split2[1])
    else:
        _curve(b, s1.outer[1])
        _curve(b, s2.outer[0])
    _curve(b, s2.outer[1])
    b.lineTo(s2.r1, 0.0)
    if _stem_serif_inlined(c):
        _n_inline_right_stem_foot(b, s2.r1, c, mm.stem)
    b.lineTo(s2.r0, 0.0)
    b.lineTo(s2.r0, mm.join_y)
    isplit2 = _split(s2.inner[0], xh, horizontal=True)
    isplit1 = _split(s1.inner[1], xh, horizontal=True)
    if isplit2 is not None:
        _curve(b, isplit2[0])
    else:
        _curve(b, s2.inner[0])
    if isplit1 is not None and isplit2 is not None:
        b.lineTo(s1.r1, xh)
        b.lineTo(s2.l0, xh)
        _curve(b, isplit1[1])
    else:
        _curve(b, s2.inner[1])
    b.lineTo(s2.l1, 0.0)
    b.lineTo(s1.r0, 0.0)
    if _stem_serif_inlined(c):
        from typekernel.parts.serifs import inline_stem_foot_serif_path

        inline_stem_foot_serif_path(b, s1.r0, 0.0, c, mm.stem)
    b.lineTo(s1.r0, mm.join_y)
    _curve(b, s1.inner[0])
    if isplit1 is not None:
        _curve(b, isplit1[0])
    else:
        _curve(b, s1.inner[1])
    b.lineTo(s1.l1, 0.0)
    b.closePath()
    cx = s2.r1 / 2.0
    half = mm.stem / 2.0
    anchors: dict[str, Pt] = {
        "top": (cx, xh),
        "bottom": (cx, 0.0),
    }
    if _stem_serif_inlined(c):
        if c.style.serif not in ("slab", "bracketed"):
            anchors["stem_L_t"] = (s1.l0 + half, xh)
    else:
        anchors["stem_L_b"] = (s1.l0 + half, 0.0)
        anchors["stem_L_t"] = (s1.l0 + half, xh)
        anchors["stem_M_b"] = ((s1.r0 + s2.l1) / 2.0, 0.0)
        anchors["stem_R_b"] = (s2.r1 - half, 0.0)
    return _pack(c, m, anchors, _ccw(b.build()))


def build_m(ctx: DesignContext, metrics: NMetrics | None = None) -> ComposedGlyph:
    return m_from_n(build_n(ctx, metrics), ctx)


def build_u(ctx: DesignContext, metrics: NMetrics | None = None) -> ComposedGlyph:
    """``u`` related to ``n``: mirrored shoulder, right stem."""
    return u_from_n(build_n(ctx, metrics), ctx)


def u_from_n(n_glyph: ComposedGlyph, ctx: DesignContext | None = None) -> ComposedGlyph:
    """Derive ``u``: the ``n`` shoulder mirrored so the bowl sits on the left.

    A 180° rotation of ``n`` left a heavy slab under the left bowl; mirroring
    across the advance swaps stems so the upright lives on the right.
    """
    c = ctx or n_glyph.context
    m = _n_record(n_glyph)
    xh = m.x_height
    # Lift inner crown like ``m`` so heavy weights keep shoulder crotch open (TK-204/207).
    um = m.tuned(
        inner_crown=min(
            max(m.inner_crown, xh),
            m.crown_y - m.stem * 0.06,
        ),
    )
    cx = um.width / 2.0
    if _italic_topology(c):
        outline = _u_branching_outline(um, c, stem_top=xh)
    else:
        outline = _u_family_outline(um, c, vf_compat=_vf_compat_stem(c))
    anchors = {
        "top": (cx, xh),
        "bottom": (cx, 0.0),
        **_n_stem_serif_anchors(
            um,
            left_top=xh,
            right_top=None,
            left_foot=False,
            left_cap=False,
            ctx=c,
            inline_right_foot=_stem_serif_inlined(c),
        ),
    }
    return _pack(c, m, anchors, outline)


def i_from_n(n_glyph: ComposedGlyph, ctx: DesignContext | None = None) -> ComposedGlyph:
    """``i``: the ``n`` stem plus a tittle."""
    c = ctx or n_glyph.context
    m = _n_record(n_glyph)
    half = m.stem / 2.0
    if _stem_serif_inlined(c):
        stem = _inline_single_stem_outline(c, m.stem, m.x_height)
        serif_anchors: dict[str, Pt] = {}
    else:
        stem = contrast_stem_caps(c, 0.0, 0.0, m.x_height, width=m.stem)
        serif_anchors = _n_stem_serif_anchors(m, left_top=m.x_height, right_foot=False)
    dot_y = m.x_height + m.stem * 0.55
    dot = tittle(c, half, dot_y, size=m.stem * 0.95)
    anchors = {
        "top": (half, m.x_height),
        "bottom": (half, 0.0),
        **serif_anchors,
    }
    return _pack(c, m, anchors, stem, dot)


def dotless_i_from_n(n_glyph: ComposedGlyph, ctx: DesignContext | None = None) -> ComposedGlyph:
    """Dotless ``ı`` (for ``i`` + accent composites)."""
    c = ctx or n_glyph.context
    m = _n_record(n_glyph)
    half = m.stem / 2.0
    if _stem_serif_inlined(c):
        outline = _inline_single_stem_outline(c, m.stem, m.x_height)
        serif_anchors: dict[str, Pt] = {}
    else:
        outline = vertical_stem(c, 0.0, 0.0, m.x_height, width=m.stem)
        serif_anchors = _n_stem_serif_anchors(m, left_top=m.x_height, right_foot=False)
    anchors = {
        "top": (half, m.x_height),
        "bottom": (half, 0.0),
        **serif_anchors,
    }
    return _pack(c, m, anchors, outline)


def dotless_j_from_n(n_glyph: ComposedGlyph, ctx: DesignContext | None = None) -> ComposedGlyph:
    """Dotless ``ȷ`` (for ``j`` + accent composites)."""
    c = ctx or n_glyph.context
    m = _n_record(n_glyph)
    height = m.x_height - c.descender
    hook = _hook_record(m, height, c)
    outline, _ = _r_outline(hook, 0.75, hook_belly=_hook_belly_fillet(m.stem))
    turned = mirror_y(mirror_x(outline, at_x=m.stem / 2.0), at_y=height / 2.0)
    body = translate(turned, 0.0, c.descender)
    dot_y = m.x_height + m.stem * 0.55
    anchors = {
        "top": (m.stem / 2.0, dot_y + m.stem * 0.95),
        "bottom": (m.stem / 2.0, c.descender),
    }
    return _pack(c, m, anchors, body)


def build_i(ctx: DesignContext, metrics: NMetrics | None = None) -> ComposedGlyph:
    """``i`` from the ``n`` stem (specimen helper and related form)."""
    return i_from_n(build_n(ctx, metrics), ctx)


def l_from_n(n_glyph: ComposedGlyph, ctx: DesignContext | None = None) -> ComposedGlyph:
    """``l``: the ``n`` stem rising to the ascender."""
    c = ctx or n_glyph.context
    m = _n_record(n_glyph)
    half = m.stem / 2.0
    stem_anchors: dict[str, Pt]
    if c.style.l_tail == "tailed":
        t = m.stem
        ext = t * 0.88
        dip = t * 0.26
        b = PathBuilder()
        b.moveTo(0.0, m.ascender)
        b.lineTo(t, m.ascender)
        b.lineTo(t, dip)
        b.curveTo(t + ext * 0.5, dip * 0.3, t + ext, dip * 0.5, t + ext, 0.0)
        b.lineTo(0.0, 0.0)
        b.closePath()
        outline = _ccw(b.build())
        stem_anchors = _vertical_stem_serif_anchors(
            m.stem, half, bottom=0.0, top=m.ascender, side="L", include_top=False
        )
    elif _stem_serif_inlined(c):
        outline = _inline_single_stem_outline(c, m.stem, m.ascender)
        stem_anchors = {}
    else:
        outline = contrast_stem_caps(c, 0.0, 0.0, m.ascender, width=m.stem)
        stem_anchors = _vertical_stem_serif_anchors(
            m.stem, half, bottom=0.0, top=m.ascender, side="L", include_top=False
        )
    anchors = {
        "top": (half, m.ascender),
        "bottom": (half, 0.0),
        **stem_anchors,
    }
    return _pack(c, m, anchors, outline)


# --- o family -----------------------------------------------------------------


def build_o(ctx: DesignContext, metrics: OMetrics | None = None) -> ComposedGlyph:
    """Control ``o``: superellipse bowl (continuous cubics) + counter."""
    m = metrics or o_metrics(ctx)
    cx, cy = m.rx, m.x_height / 2.0
    outer, hole = bowl(
        ctx,
        cx,
        cy,
        rx=m.rx,
        ry=m.ry,
        thickness_v=m.thickness_v,
        thickness_h=m.thickness_h,
        shape="superellipse",
        n=m.exponent,
    )
    return (
        GlyphAssembler(ctx)
        .with_design(m)
        .add(outer)
        .add_hole(hole)
        .subtract_holes()
        .anchor("top", cx, m.x_height)
        .anchor("bottom", cx, 0.0)
        .build()
    )


def _cubic_pts(c: tuple[Point, Point, Point, Point]) -> Cubic:
    return (c[0].as_tuple(), c[1].as_tuple(), c[2].as_tuple(), c[3].as_tuple())


def _quarters(cx: float, cy: float, rx: float, ry: float, n: float) -> list[Cubic]:
    """Four CCW superellipse quadrants from ``+x`` as point tuples."""
    return [_cubic_pts(q) for q in superellipse_cubics(cx, cy, rx, ry, n)]


def _scale_x(c: Cubic, about: float, f: float) -> Cubic:
    return (
        (about + (c[0][0] - about) * f, c[0][1]),
        (about + (c[1][0] - about) * f, c[1][1]),
        (about + (c[2][0] - about) * f, c[2][1]),
        (about + (c[3][0] - about) * f, c[3][1]),
    )


def _bowl_stem_outline(
    o: OMetrics,
    stem: float,
    *,
    stem_bottom: float,
    stem_top: float,
    join: float,
    foot: Callable[[PathBuilder, float], None] | None = None,
) -> Outline:
    """``d``-type bowl (left) + stem (right) as two contours, outer CCW.

    The outer is the ``o`` bowl with its right side cut where it meets the
    stem's left face. The counter keeps the ``o`` counter's left half; its
    right half is stretched to the stem face so the counter has a straight
    inner stem, with the bowl ``join`` × its thickness where it meets it.

    ``foot(builder, stem_left_x)`` replaces the stem's left face below the
    bowl; it must end on ``(stem_left_x, stem_bottom)`` (``g`` draws its hook).
    """
    cx, cy = o.rx, o.x_height / 2.0
    s_r = cx + o.rx
    s_l = s_r - stem
    if s_l <= cx:
        raise ValueError("stem is wider than half the bowl; widen the o or thin the stem")

    q0, q1, q2, q3 = _quarters(cx, cy, o.rx, o.ry, o.exponent)
    top_cut = _split(q0, s_l, horizontal=False)
    bot_cut = _split(q3, s_l, horizontal=False)
    if top_cut is None or bot_cut is None:  # pragma: no cover - s_l inside bowl
        raise ValueError("stem face does not cross the bowl")
    y_t, y_b = top_cut[1][0][1], bot_cut[0][3][1]
    # Very bold stems meet the bowl beyond the stem ends; extend the stem.
    stem_top, stem_bottom = max(stem_top, y_t), min(stem_bottom, y_b)

    irx, iry = o.rx - o.thickness_v, o.ry - o.thickness_h
    iq0, iq1, iq2, iq3 = _quarters(cx, cy, irx, iry, o.exponent)
    flat = max(0.05, min(0.95, (y_t - join * o.thickness_v - cy) / iry))
    e = o.exponent
    q = 1.0 - (1.0 - flat**e) ** (1.0 / e)
    reach = (s_l - cx) / (1.0 - q)
    f = reach / irx
    i_top = _split(_scale_x(iq0, cx, f), s_l, horizontal=False)
    i_bot = _split(_scale_x(iq3, cx, f), s_l, horizontal=False)
    if i_top is None or i_bot is None:  # pragma: no cover - reach > s_l - cx
        raise ValueError("counter does not reach the stem face")

    b = PathBuilder()
    b.moveTo(s_r, stem_bottom)
    b.lineTo(s_r, stem_top)
    top_join = top_cut[1]
    p0 = top_join[0]
    if abs(p0[0] - s_l) > 1e-9:
        top_join = ((s_l, p0[1]), top_join[1], top_join[2], top_join[3])
    b.lineTo(s_l, stem_top)
    b.lineTo(*top_join[0])
    _curve(b, top_join)
    _curve(b, q1)
    _curve(b, q2)
    bot_join = bot_cut[0]
    p_end = bot_join[3]
    if abs(p_end[0] - s_l) > 1e-9:
        bot_join = (bot_join[0], bot_join[1], bot_join[2], (s_l, p_end[1]))
    _curve(b, bot_join)
    if foot is None:
        b.lineTo(s_l, stem_bottom)
    else:
        foot(b, s_l)
    b.closePath()
    b.moveTo(*i_bot[0][3])
    b.lineTo(*i_top[1][0])
    _curve(b, i_top[1])
    _curve(b, iq1)
    _curve(b, iq2)
    _curve(b, i_bot[0])
    b.closePath()
    outer, counter = b.build().contours
    return Outline((outer, reverse_contour(counter)))


def _bowl_glyph(
    o_glyph: ComposedGlyph,
    n_glyph: ComposedGlyph | None,
    ctx: DesignContext | None,
    *,
    stem_left: bool,
    descends: bool,
    join: float,
) -> ComposedGlyph:
    c = ctx or o_glyph.context
    o = _o_record(o_glyph)
    stem = _n_record(n_glyph).stem if n_glyph is not None else o.thickness
    if descends:
        bottom, top = c.descender, o.x_height
    else:
        bottom, top = 0.0, (_n_record(n_glyph).ascender if n_glyph is not None else c.ascender)
    foot: Callable[[PathBuilder, float], None] | None = None
    if c.style.serif == "bracketed":
        from typekernel.parts.serifs import inline_stem_foot_serif_path

        y_foot = bottom

        def foot(b: PathBuilder, x_stem: float) -> None:
            inline_stem_foot_serif_path(b, x_stem, y_foot, c, stem)

    outline = _bowl_stem_outline(
        o, stem, stem_bottom=bottom, stem_top=top, join=join, foot=foot
    )
    cx = o.rx
    anchors: dict[str, Pt] = {"top": (cx, o.x_height)}
    if not descends:
        anchors["bottom"] = (cx, 0.0)
    if stem_left:
        outline = Outline(tuple(reverse_contour(k) for k in mirror_x(outline, at_x=cx).contours))
    return _pack(c, o, anchors, outline)


def d_from_o(
    o_glyph: ComposedGlyph,
    n_glyph: ComposedGlyph | None = None,
    ctx: DesignContext | None = None,
    *,
    join: float = 0.85,
) -> ComposedGlyph:
    """Derive ``d``: the ``o`` bowl with the ``n`` stem rising on the right.

    ``join`` is the bowl's thickness where it meets the stem, as a fraction of
    the ``o`` thickness (below 1 thins the junction, as designers do).
    """
    return _bowl_glyph(o_glyph, n_glyph, ctx, stem_left=False, descends=False, join=join)


def b_from_o(
    o_glyph: ComposedGlyph,
    n_glyph: ComposedGlyph | None = None,
    ctx: DesignContext | None = None,
    *,
    join: float = 0.85,
) -> ComposedGlyph:
    """Derive ``b``: mirror of ``d`` (stem on the left)."""
    return _bowl_glyph(o_glyph, n_glyph, ctx, stem_left=True, descends=False, join=join)


def q_from_o(
    o_glyph: ComposedGlyph,
    n_glyph: ComposedGlyph | None = None,
    ctx: DesignContext | None = None,
    *,
    join: float = 0.85,
) -> ComposedGlyph:
    """Derive ``q``: the ``o`` bowl with the stem descending on the right."""
    return _bowl_glyph(o_glyph, n_glyph, ctx, stem_left=False, descends=True, join=join)


def p_from_o(
    o_glyph: ComposedGlyph,
    n_glyph: ComposedGlyph | None = None,
    ctx: DesignContext | None = None,
    *,
    join: float = 0.85,
) -> ComposedGlyph:
    """Derive ``p``: mirror of ``q`` (stem descending on the left)."""
    return _bowl_glyph(o_glyph, n_glyph, ctx, stem_left=True, descends=True, join=join)


def _single_storey_a_from_o(
    o_glyph: ComposedGlyph,
    n_glyph: ComposedGlyph | None,
    c: DesignContext,
    *,
    join: float,
) -> ComposedGlyph:
    o = _o_record(o_glyph)
    if _italic_topology(c):
        o = o.tuned(rx=o.rx * 0.965, ry=o.ry * 0.985)
    stem = _n_record(n_glyph).stem if n_glyph is not None else o.thickness
    outline = _bowl_stem_outline(o, stem, stem_bottom=0.0, stem_top=o.x_height, join=join)
    outline = apply_terminal_shear(c, outline, at=(2.0 * o.rx - stem * 0.35, o.x_height * 0.92))
    anchors = {
        "top": (o.rx, o.x_height),
        "bottom": (o.rx, 0.0),
        "ogonek": (2.0 * o.rx - stem / 2.0, 0.0),
    }
    return _pack(c, o, anchors, outline)


def _double_storey_blend_radius(c: DesignContext) -> float:
    """Cap join fillet so heavy stems do not split two-storey VF outlines."""
    return min(max(2.0, c.join_radius * 0.45), c.stem * 0.08)


def _segment_to_cubic(seg: LineSegment | CubicSegment) -> Cubic:
    if isinstance(seg, CubicSegment):
        pts = seg.points
        return (
            pts[0].as_tuple(),
            pts[1].as_tuple(),
            pts[2].as_tuple(),
            pts[3].as_tuple(),
        )
    p0, p1 = seg.p0.as_tuple(), seg.p1.as_tuple()
    return (
        p0,
        (p0[0] + (p1[0] - p0[0]) / 3.0, p0[1] + (p1[1] - p0[1]) / 3.0),
        (p0[0] + 2.0 * (p1[0] - p0[0]) / 3.0, p0[1] + 2.0 * (p1[1] - p0[1]) / 3.0),
        p1,
    )


def _contour_cubics(contour: Contour) -> list[Cubic]:
    return [_segment_to_cubic(seg) for seg in contour.segments]


def _superellipse_x_at_y(cx: float, cy: float, rx: float, ry: float, n: float, y: float) -> float:
    """Right-side ``x`` where the superellipse crosses horizontal ``y``."""
    t = abs((y - cy) / ry) ** n
    if t > 1.0 + 1e-9:
        raise ValueError(f"y={y} outside superellipse vertical range")
    return float(cx + rx * (1.0 - t) ** (1.0 / n))


def _append_bowl_outer_ccw(
    b: PathBuilder,
    bowl_outer: Outline,
    *,
    shelf_y: float,
) -> None:
    """Trace lower bowl outer CCW from the right shelf around to the baseline toe."""
    cubics = _contour_cubics(bowl_outer.contours[0])
    n = len(cubics)
    start: Cubic | None = None
    start_idx = -1
    for i, c in enumerate(cubics):
        hit = _split(c, shelf_y, horizontal=True)
        if hit is None:
            continue
        lo, hi = hit
        start = hi if hi[3][1] > lo[3][1] else lo
        start_idx = i
        break
    if start is None or start_idx < 0:
        raise ValueError("bowl outer does not cross shelf_y")
    _curve(b, start)
    for j in range(1, n):
        c = cubics[(start_idx + j) % n]
        _curve(b, c)
        if abs(c[3][1]) < 1e-6:
            return
    raise ValueError("bowl outer did not reach baseline")


def _double_storey_a_outline(
    c: DesignContext,
    o: OMetrics,
    mm: NMetrics,
    s: _Shoulder,
    bowl_outer: Outline,
    *,
    bowl_cx: float,
    bowl_cy: float,
    bowl_rx: float,
    bowl_ry: float,
    sx0: float,
    sx1: float,
    xh: float,
    bowl_join: float,
) -> Outline:
    """Single CCW outer for two-storey ``a`` (no boolean union; TK-305 VF)."""
    n_exp = o.exponent
    shelf_x = _superellipse_x_at_y(bowl_cx, bowl_cy, bowl_rx, bowl_ry, n_exp, bowl_join)
    exit_x = _superellipse_x_at_y(bowl_cx, bowl_cy, bowl_rx, bowl_ry, n_exp, 0.0)

    b = PathBuilder()
    b.moveTo(sx1, 0.0)
    b.lineTo(sx1, xh)
    b.lineTo(sx1, mm.leg_top)
    _curve(b, s.outer[1])
    _curve(b, s.outer[0])
    b.lineTo(sx0, bowl_join)
    # Keep a horizontal shelf segment at every weight (heavy bowls meet the stem early).
    shelf_landing = shelf_x if shelf_x < sx0 - 1e-6 else sx0 - max(mm.stem * 0.04, 2.0)
    b.lineTo(shelf_landing, bowl_join)
    _append_bowl_outer_ccw(b, bowl_outer, shelf_y=bowl_join)
    if exit_x < sx1 - 1e-6:
        b.lineTo(sx1, 0.0)
    b.closePath()
    return _ccw(b.build())


def _merge_solid_contours(outline: Outline) -> Outline:
    contours = list(outline.contours)
    big = [ct for ct in contours if len(ct.segments) >= 6]
    if big and len(big) < len(contours):
        contours = big
    if len(contours) <= 1:
        return Outline(tuple(contours))
    from typekernel.geo.boolean import union_all

    return union_all([Outline((ct,)) for ct in contours])


def _vf_ready_composed(glyph: ComposedGlyph) -> ComposedGlyph:
    from typekernel.geo.outline import normalize_master_outline

    solids = tuple(
        normalize_master_outline(_merge_solid_contours(s)) for s in glyph.solids
    )
    return replace(glyph, solids=solids)


def _double_storey_a_from_o(
    o_glyph: ComposedGlyph,
    n_glyph: ComposedGlyph | None,
    c: DesignContext,
) -> ComposedGlyph:
    """Two-storey ``a``: lower bowl, upper arch, right stem (TK-305)."""
    o = _o_record(o_glyph)
    m = _n_record(n_glyph) if n_glyph is not None else n_metrics(c)
    stem = m.stem
    xh = o.x_height
    width = 2.0 * o.rx
    sx0, sx1 = width - stem, width

    bowl_ry = xh * 0.36
    bowl_rx = bowl_ry * (o.rx / o.ry) * 0.9
    bowl_cx = bowl_rx + stem * 0.38
    bowl_cy = bowl_ry
    lower_outer, lower_hole = bowl(
        c,
        bowl_cx,
        bowl_cy,
        rx=bowl_rx,
        ry=bowl_ry,
        thickness_v=stem * 0.96,
        thickness_h=stem * c.contrast * 0.96,
        shape="superellipse",
        n=o.exponent,
    )
    x0 = sx0 - m.counter - stem
    join_y = bowl_cy + bowl_ry * 0.38
    mm = m.tuned(
        join_y=join_y,
        crown_y=xh + c.overshoot * 0.28,
        leg_top=xh - stem * 0.06,
        inner_crown=xh * 0.74,
    )
    s = _shoulder(mm, x0)
    bowl_join = bowl_cy + bowl_ry * 0.68

    bi = PathBuilder()
    bi.moveTo(sx0, bowl_join)
    bi.lineTo(sx0, mm.join_y)
    bi.lineTo(s.r0, mm.join_y)
    _curve(bi, s.inner[0])
    _curve(bi, s.inner[1])
    bi.lineTo(sx0, mm.join_y)
    bi.lineTo(sx0, bowl_join)
    bi.closePath()
    upper_ct = bi.build().contours[0]
    upper_eye = Outline(
        (reverse_contour(upper_ct) if signed_area(upper_ct) > 0 else upper_ct,)
    )
    lower_ct = lower_hole.contours[0]
    lower_hole = Outline(
        (reverse_contour(lower_ct) if signed_area(lower_ct) > 0 else lower_ct,)
    )

    glyph = (
        GlyphAssembler(c)
        .with_design(o)
        .add(
            _double_storey_a_outline(
                c,
                o,
                mm,
                s,
                lower_outer,
                bowl_cx=bowl_cx,
                bowl_cy=bowl_cy,
                bowl_rx=bowl_rx,
                bowl_ry=bowl_ry,
                sx0=sx0,
                sx1=sx1,
                xh=xh,
                bowl_join=bowl_join,
            )
        )
        .add_hole(lower_hole)
        .add_hole(upper_eye)
        .anchor("top", width * 0.46, xh)
        .anchor("bottom", bowl_cx, 0.0)
        .anchor("ogonek", sx0 + stem / 2.0, 0.0)
        .build()
    )
    return _vf_ready_composed(glyph)


def a_from_o(
    o_glyph: ComposedGlyph,
    n_glyph: ComposedGlyph | None = None,
    ctx: DesignContext | None = None,
    *,
    join: float = 0.85,
) -> ComposedGlyph:
    """Derive ``a`` (single- or double-storey per ``ctx.style.a_form``)."""
    c = ctx or o_glyph.context
    if c.style.a_form == "double":
        return _double_storey_a_from_o(o_glyph, n_glyph, c)
    return _single_storey_a_from_o(o_glyph, n_glyph, c, join=join)


def _rev(c: Cubic) -> Cubic:
    return (c[3], c[2], c[1], c[0])


def _rotate_cubic(c: Cubic, degrees: float, ox: float, oy: float) -> Cubic:
    rad = math.radians(degrees)
    co, si = math.cos(rad), math.sin(rad)

    def rot(pt: Pt) -> Pt:
        x, y = pt[0] - ox, pt[1] - oy
        return (ox + x * co - y * si, oy + x * si + y * co)

    return (rot(c[0]), rot(c[1]), rot(c[2]), rot(c[3]))


def _ring(o: OMetrics, ctx: DesignContext) -> tuple[list[Cubic], list[Cubic]]:
    """Outer and counter quadrants of the ``o`` ring (CCW from ``+x``)."""
    cx, cy = o.rx, o.x_height / 2.0
    outer = _quarters(cx, cy, o.rx, o.ry, o.exponent)
    inner = _quarters(cx, cy, o.rx - o.thickness_v, o.ry - o.thickness_h, o.exponent)
    if abs(ctx.stress) > 1e-9:
        inner = [_rotate_cubic(c, ctx.stress, cx, cy) for c in inner]
    return outer, inner


def _terminal_x(o: OMetrics, aperture: float, closure: float) -> float:
    """Vertical terminal cut: opens toward the centre as ``aperture`` grows."""
    ap = max(0.0, min(1.0, aperture))
    return o.rx + (o.rx - o.thickness_v) * (0.95 - closure * ap)


def _opening_slab_metrics(c: DesignContext, o: OMetrics) -> tuple[float, float]:
    """Horizontal caps on vertical ``c``/``G`` opening terminals (+x slab)."""
    from typekernel.parts.serifs import serif_metrics

    length, thick, _ = serif_metrics(c)
    cap = o.x_height
    l = min(length * 0.35, o.thickness_v * 0.55, c.stem * 0.28)
    th = min(thick * 0.55, cap * 0.04, c.stem * 0.1)
    if c.stem > 150.0:
        l = min(l, o.thickness_v * 0.42)
        th = min(th, cap * 0.032, o.thickness_h * 0.35)
    return l, th


def _opening_top_slab_move(b: PathBuilder, pt: Pt, length: float, thick: float) -> None:
    tx, ty = pt
    b.moveTo(tx + length, ty + thick)
    b.lineTo(tx + length, ty)
    b.lineTo(tx, ty)


def _opening_bottom_slab_detour(b: PathBuilder, pt: Pt, length: float, thick: float) -> None:
    """Bottom opening shelf (+x); shallow vertical to avoid bowl overlap at bold."""
    tx, ty = pt
    b.lineTo(tx + length, ty)
    b.lineTo(tx + length, ty - thick * 0.55)
    b.lineTo(tx, ty - thick * 0.55)


def _opening_top_bracketed_move(
    b: PathBuilder, pt: Pt, length: float, thick: float, bracket_r: float
) -> None:
    """Opening terminal shelf (+x) with cubic bracket at the outer corner."""
    tx, ty = pt
    xl, xr, y = tx, tx + length, ty
    b.moveTo(xr, y)
    b.lineTo(xr, y + thick)
    span_x = xr - xl
    r = min(bracket_r, span_x * 0.4, thick * 0.45)
    if r < 0.35:
        b.lineTo(xl, y + thick)
        b.lineTo(xl, y)
        return
    b.lineTo(xl + r, y + thick)
    b.curveTo(
        xl + r - r * KAPPA,
        y + thick,
        xl,
        y + thick - r + r * KAPPA,
        xl,
        y + thick - r,
    )
    b.lineTo(xl, y)


def _opening_bottom_bracketed_detour(
    b: PathBuilder, pt: Pt, length: float, thick: float, bracket_r: float
) -> None:
    """Bottom opening shelf (+x) with cubic bracket (shallow shelf like slab)."""
    tx, ty = pt
    shelf = thick * 0.55
    b.lineTo(tx + length, ty)
    r = min(bracket_r, length * 0.4, shelf * 0.45)
    if r < 0.35:
        b.lineTo(tx + length, ty - shelf)
        b.lineTo(tx, ty - shelf)
        return
    b.lineTo(tx + length, ty - shelf + r)
    b.curveTo(
        tx + length,
        ty - shelf + r - r * KAPPA,
        tx + length - r + r * KAPPA,
        ty - shelf,
        tx + length - r,
        ty - shelf,
    )
    b.lineTo(tx, ty - shelf)


def _cut(c: Cubic, where: float, *, horizontal: bool) -> tuple[Cubic, Cubic]:
    pieces = _split(c, where, horizontal=horizontal)
    if pieces is None:
        axis = "y" if horizontal else "x"
        raise ValueError(f"curve does not cross {axis}={where:.2f}; check o metrics")
    return pieces


def c_from_o(
    o_glyph: ComposedGlyph,
    ctx: DesignContext | None = None,
    *,
    aperture: float | None = None,
) -> ComposedGlyph:
    """Derive ``c``: the ``o`` ring opened on the right with vertical terminals.

    ``aperture`` (default: the context's) moves both cuts toward the centre.
    One contour: outer arc, terminal, counter arc back, terminal.
    """
    c = ctx or o_glyph.context
    o = _o_record(o_glyph)
    (q0, q1, q2, q3), (i0, i1, i2, i3) = _ring(o, c)
    ap = c.aperture if aperture is None else aperture
    x_t = _terminal_x(o, ap, opening_closure(c, 0.55))
    top = _cut(q0, x_t, horizontal=False)[1]
    bot = _cut(q3, x_t, horizontal=False)[0]
    itop = _cut(i0, x_t, horizontal=False)[1]
    ibot = _cut(i3, x_t, horizontal=False)[0]

    b = PathBuilder()
    slab_l, slab_th = 0.0, 0.0
    bracket_r = 0.0
    if c.style.serif in ("slab", "bracketed"):
        slab_l, slab_th = _opening_slab_metrics(c, o)
    if c.style.serif == "bracketed":
        from typekernel.parts.serifs import serif_metrics

        _, _, bracket_r = serif_metrics(c)
        _opening_top_bracketed_move(b, top[0], slab_l, slab_th, bracket_r)
    elif c.style.serif == "slab":
        _opening_top_slab_move(b, top[0], slab_l, slab_th)
    else:
        b.moveTo(*top[0])
    for cubic in (top, q1, q2, bot):
        _curve(b, cubic)
    if c.style.serif == "bracketed":
        _opening_bottom_bracketed_detour(b, bot[3], slab_l, slab_th, bracket_r)
    elif c.style.serif == "slab":
        _opening_bottom_slab_detour(b, bot[3], slab_l, slab_th)
    b.lineTo(*ibot[3])
    for cubic in (_rev(ibot), _rev(i2), _rev(i1), _rev(itop)):
        _curve(b, cubic)
    b.closePath()
    anchors = {"top": (o.rx, o.x_height), "bottom": (o.rx, 0.0)}
    return _pack(c, o, anchors, _ccw(b.build()))


def e_from_o(
    o_glyph: ComposedGlyph,
    ctx: DesignContext | None = None,
    *,
    aperture: float | None = None,
    bar_raise: float = 0.25,
) -> ComposedGlyph:
    """Derive ``e``: the ``o`` ring with a crossbar and a lower aperture.

    The bar (``o`` thickness × context contrast) sits ``bar_raise`` × its
    thickness above the centre and runs from the inner left wall to the outer
    right edge. Below it the ring is cut at a vertical lower terminal, so the
    lower counter opens into the aperture. Two contours: outer and eye.
    """
    c = ctx or o_glyph.context
    o = _o_record(o_glyph)
    (q0, q1, q2, q3), (i0, i1, i2, i3) = _ring(o, c)
    cy = o.x_height / 2.0
    # Heavy weights thin the bar so it still fits inside the counter.
    room = 0.75 * (o.ry - o.thickness_h)
    bar_t = min(o.thickness_h * _horizontal_slant_scale(c), 1.2 * room)
    raise_ = max(-0.45, min(0.45, bar_raise)) * bar_t
    raise_ = max(-(room - bar_t / 2.0), min(room - bar_t / 2.0, raise_))
    bar_bot, bar_top = cy + raise_ - bar_t / 2.0, cy + raise_ + bar_t / 2.0
    x_t = _terminal_x(
        o, c.aperture if aperture is None else aperture, opening_closure(c, 0.45)
    )

    below, right = _cut(q3, bar_bot, horizontal=True)
    lower = _cut(below, x_t, horizontal=False)[0]
    ilower = _cut(i3, x_t, horizontal=False)[0]
    iwall = _cut(i2, bar_bot, horizontal=True)[1]

    b = PathBuilder()
    b.moveTo(*right[0])
    for cubic in (right, q0, q1, q2, lower):
        _curve(b, cubic)
    if c.style.serif in ("slab", "bracketed"):
        slab_l, slab_th = _opening_slab_metrics(c, o)
        if c.style.serif == "bracketed":
            from typekernel.parts.serifs import serif_metrics

            _, _, bracket_r = serif_metrics(c)
            _opening_bottom_bracketed_detour(b, lower[3], slab_l, slab_th, bracket_r)
        else:
            _opening_bottom_slab_detour(b, lower[3], slab_l, slab_th)
    b.lineTo(*ilower[3])
    _curve(b, _rev(ilower))
    _curve(b, _rev(iwall))
    b.closePath()

    eye_r = _cut(i0, bar_top, horizontal=True)[1]
    eye_l = _cut(i1, bar_top, horizontal=True)[0]
    b.moveTo(*eye_r[0])
    _curve(b, eye_r)
    _curve(b, eye_l)
    b.closePath()

    outer, eye = b.build().contours
    outline = Outline((outer, reverse_contour(eye)))
    shear = _e_oblique_shear(c)
    if shear is not None:
        from typekernel.geo.extrema import outline_e_oblique_splits

        outline = outline_e_oblique_splits(outline, shear)
    anchors = {"top": (o.rx, o.x_height), "bottom": (o.rx, 0.0)}
    return _pack(c, o, anchors, outline)


def _double_storey_g_from_o(
    o_glyph: ComposedGlyph,
    n_glyph: ComposedGlyph | None,
    c: DesignContext,
) -> ComposedGlyph:
    """Two-storey ``g``: upper bowl, descender loop, right link (TK-305)."""
    o = _o_record(o_glyph)
    m = _n_record(n_glyph) if n_glyph is not None else n_metrics(c)
    stem, desc, xh = m.stem, c.descender, o.x_height
    width = 2.0 * o.rx
    sx0 = width - stem
    tv, th = stem * 0.96, stem * c.contrast * 0.96

    upper_ry = xh * 0.24
    upper_rx = upper_ry * (o.rx / o.ry) * 0.92
    upper_cx = upper_rx + stem * 0.4
    upper_cy = xh - upper_ry * 0.72
    upper_outer, upper_hole = bowl(
        c,
        upper_cx,
        upper_cy,
        rx=upper_rx,
        ry=upper_ry,
        thickness_v=tv,
        thickness_h=th,
        shape="superellipse",
        n=o.exponent,
    )

    lower_ry = xh * 0.34
    lower_rx = lower_ry * (o.rx / o.ry) * 0.9
    lower_cx = upper_cx
    lower_cy = desc + lower_ry * 1.08
    lower_outer, lower_hole = bowl(
        c,
        lower_cx,
        lower_cy,
        rx=lower_rx,
        ry=lower_ry,
        thickness_v=tv,
        thickness_h=th,
        shape="superellipse",
        n=o.exponent,
    )

    stem_bottom = lower_cy + lower_ry * 0.35
    stem_o = contrast_stem_caps(c, sx0, stem_bottom, xh, width=stem * 1.02)
    counters = Outline(
        tuple(
            reverse_contour(contour)
            for hole in (upper_hole, lower_hole)
            for contour in hole.contours
        )
    )

    glyph = (
        GlyphAssembler(c)
        .with_design(o)
        .add(stem_o)
        .add(upper_outer)
        .add(lower_outer)
        .add_hole(counters)
        .union_solids()
        .blend_joins(_double_storey_blend_radius(c))
        .anchor("top", upper_cx, xh)
        .anchor("bottom", lower_cx, desc)
        .build()
    )
    return _vf_ready_composed(glyph)


def _g_hook_join_y(stem: float, join_y: float, inner_crown: float) -> float:
    """Raise the descender hook crotch on heavy stems (VF-safe, no extra segments)."""
    if stem <= 110.0:
        return join_y
    headroom = inner_crown - 0.25 * stem - join_y
    lift = min((stem - 110.0) * 0.55, headroom)
    return join_y + max(0.0, lift)


def _hook_belly_fillet(stem: float) -> float:
    """Cubic belly detour scale on hook letters (replaces ``blend_corners``)."""
    return max(stem * 0.065, 4.5)


def _g_hook_belly_fillet(stem: float) -> float:
    return _hook_belly_fillet(stem)


def g_from_o(
    o_glyph: ComposedGlyph,
    n_glyph: ComposedGlyph | None = None,
    ctx: DesignContext | None = None,
    *,
    arm: float = 0.75,
    join: float = 0.85,
) -> ComposedGlyph:
    """Derive ``g`` (single-storey hook or double-storey bowls per ``style.g_form``)."""
    c = ctx or o_glyph.context
    if c.style.g_form == "double":
        return _double_storey_g_from_o(o_glyph, n_glyph, c)
    o = _o_record(o_glyph)
    nm = _n_record(n_glyph) if n_glyph is not None else n_metrics(c)
    from typekernel.parts.weight_relief import stem_weight_fraction

    stem, desc = nm.stem, c.descender
    t_relief = stem_weight_fraction(stem)
    if t_relief > 0.55:
        o_nom = o_metrics(c)
        blend = min(1.0, (t_relief - 0.55) / 0.38) * 0.48
        o = o.tuned(
            rx=o.rx + blend * (o_nom.rx - o.rx),
            ry=o.ry + blend * (o_nom.ry - o.ry),
        )
    height = o.x_height - desc
    ease = min(1.0, max(0.0, (c.roundness - 0.30) / 0.18))
    hook_depth = 0.45 - 0.24 * t_relief * ease
    hook = _hook_record(nm, height, c, depth=hook_depth)
    join_y = _g_hook_join_y(stem, hook.join_y, hook.inner_crown)
    if join_y != hook.join_y:
        hook = hook.tuned(join_y=join_y)
    # The hook's crotch must sit below where the bowl meets the stem; heavy
    # weights get a thinner hook rather than an outline that folds back.
    s_l = 2.0 * o.rx - stem
    bowl_meets = _cut(_ring(o, c)[0][3], s_l, horizontal=False)[0][3][1]
    join_needed = height + desc - (bowl_meets - 0.2 * stem)
    if hook.join_y < join_needed:
        inner_crown = max(hook.inner_crown, join_needed + 0.35 * stem)
        hook = hook.tuned(join_y=join_needed, inner_crown=min(inner_crown, hook.crown_y - 1.0))
    s, outer_arm, inner_arm, _ = _r_pieces(hook, arm)

    def foot(b: PathBuilder, s_l: float) -> None:
        def turn(p: Pt) -> Pt:
            return (s_l + stem - p[0], height - p[1] + desc)

        def turned(cu: Cubic) -> Cubic:
            r = _rev(cu)
            return (turn(r[0]), turn(r[1]), turn(r[2]), turn(r[3]))

        b.lineTo(*turn(s.inner[1][3]))
        _curve(b, turned(s.inner[1]))
        _curve(b, turned(inner_arm))
        bulge = _g_hook_belly_fillet(stem)
        p_here = turn(inner_arm[0])
        p_out = turn(outer_arm[3])
        b.curveTo(
            p_here[0] - bulge * 0.35,
            p_here[1] - bulge * 0.15,
            p_out[0],
            p_out[1] + bulge * 0.2,
            p_out[0],
            p_out[1],
        )
        _curve(b, turned(outer_arm))
        _curve(b, turned(s.outer[0]))

    outline = apply_terminal_shear(
        c,
        _bowl_stem_outline(o, stem, stem_bottom=desc, stem_top=o.x_height, join=join, foot=foot),
    )
    return _pack(c, o, {"top": (o.rx, o.x_height)}, outline)


S_OPENING_REACH_RELIEF = 0.012  # TK-206 / appendix B-15 (golden-linked)


def s_from_o(
    o_glyph: ComposedGlyph,
    ctx: DesignContext | None = None,
    *,
    aperture: float | None = None,
    width: float = 0.82,
    top_scale: float = 0.90,
    spine: float = 0.50,
) -> ComposedGlyph:
    """Derive ``s``: two stacked half-rings sharing the spine.

    The upper ring keeps its left half and opens at the upper right; the
    lower ring keeps its right half and opens at the lower left. The upper
    ring's bottom stroke *is* the lower ring's top stroke, so the spine is
    smooth at ``spine`` × x-height. The lower ring is ``width`` × the ``o``,
    the upper ``top_scale`` × narrower. Strokes thin in heavy weights so the
    counters stay open. One contour.
    """
    c = ctx or o_glyph.context
    o = _o_record(o_glyph)
    xh, os_, e = o.x_height, o.overshoot, o.exponent
    ym = spine * xh
    rx_l = width * o.rx
    rx_u = rx_l * top_scale
    tv = min(o.thickness_h, 0.3 * xh)
    ry_u = (xh + os_ - ym + tv / 2.0) / 2.0
    ry_l = (ym + tv / 2.0 + os_) / 2.0
    tv = min(tv, 0.6 * min(ry_u, ry_l))
    ry_u = (xh + os_ - ym + tv / 2.0) / 2.0
    ry_l = (ym + tv / 2.0 + os_) / 2.0
    th = min(o.thickness_v, 0.6 * rx_u)
    cx = rx_l
    cy_u, cy_l = xh + os_ - ry_u, ry_l - os_

    u0, u1, u2, _ = _quarters(cx, cy_u, rx_u, ry_u, e)
    ui0, ui1, ui2, _ = _quarters(cx, cy_u, rx_u - th, ry_u - tv, e)
    l0, _, l2, l3 = _quarters(cx, cy_l, rx_l, ry_l, e)
    li0, _, li2, li3 = _quarters(cx, cy_l, rx_l - th, ry_l - tv, e)

    ap = max(0.0, min(1.0, c.aperture if aperture is None else aperture))
    reach = min(0.99, s_opening_factor(c, ap) + S_OPENING_REACH_RELIEF)
    x_tu = cx + (rx_u - th) * reach
    x_tl = cx - (rx_l - th) * reach
    u_top = _cut(u0, x_tu, horizontal=False)[1]
    ui_top = _cut(ui0, x_tu, horizontal=False)[1]
    l_bot = _cut(l2, x_tl, horizontal=False)[1]
    li_bot = _cut(li2, x_tl, horizontal=False)[1]

    b = PathBuilder()
    slab_l, slab_th = 0.0, 0.0
    bracket_r = 0.0
    if c.style.serif in ("slab", "bracketed"):
        slab_l, slab_th = _opening_slab_metrics(c, o)
    if c.style.serif == "bracketed":
        from typekernel.parts.serifs import serif_metrics

        _, _, bracket_r = serif_metrics(c)
        _opening_top_bracketed_move(b, u_top[0], slab_l, slab_th, bracket_r)
    elif c.style.serif == "slab":
        _opening_top_slab_move(b, u_top[0], slab_l, slab_th)
    else:
        b.moveTo(*u_top[0])
    for cubic in (u_top, u1, u2, _rev(li0), _rev(li3), _rev(li_bot)):
        _curve(b, cubic)
    b.lineTo(*l_bot[0])
    if c.style.serif == "bracketed":
        _opening_bottom_bracketed_detour(b, l_bot[0], slab_l, slab_th, bracket_r)
    elif c.style.serif == "slab":
        _opening_bottom_slab_detour(b, l_bot[0], slab_l, slab_th)
    for cubic in (l_bot, l3, l0, _rev(ui2), _rev(ui1), _rev(ui_top)):
        _curve(b, cubic)
    b.closePath()
    anchors = {"top": (cx, xh), "bottom": (cx, 0.0)}
    return _pack(c, o, anchors, _ccw(b.build()))


def _from_controls(
    derive: Callable[[ComposedGlyph, ComposedGlyph | None], ComposedGlyph],
) -> Callable[[DesignContext], ComposedGlyph]:
    return lambda ctx: derive(build_o(ctx), build_n(ctx))


CONTROL_BUILDERS: dict[str, Callable[[DesignContext], ComposedGlyph]] = {
    "n": build_n,
    "h": build_h,
    "m": build_m,
    "r": build_r,
    "o": build_o,
    "u": build_u,
    "i": build_i,
    "l": lambda ctx: l_from_n(build_n(ctx)),
    "b": _from_controls(b_from_o),
    "d": _from_controls(d_from_o),
    "p": _from_controls(p_from_o),
    "q": _from_controls(q_from_o),
    "a": _from_controls(a_from_o),
    "c": lambda ctx: c_from_o(build_o(ctx)),
    "e": lambda ctx: e_from_o(build_o(ctx)),
}

def build_control_letter(ch: str, ctx: DesignContext) -> ComposedGlyph:
    key = ch.lower()
    try:
        return CONTROL_BUILDERS[key](ctx)
    except KeyError as exc:
        raise KeyError(
            f"no control/related builder for {ch!r}; have {sorted(CONTROL_BUILDERS)}"
        ) from exc


def build_control_word(text: str, ctx: DesignContext) -> list[ComposedGlyph]:
    return [build_control_letter(ch, ctx) for ch in text]
