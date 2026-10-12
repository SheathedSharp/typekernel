"""Control glyphs and related forms — type-designer workflow.

Order: proportions (:class:`~typekernel.parts.context.DesignContext`) →
control letters as **continuous cubic outlines** → derive related forms →
optical / class spacing (elsewhere).

This replaces CAD boolean trough recipes (``stem ∪ arch_slot ∪ stem``) for
``n`` / ``h`` / ``o``. Pen-expand and Assembler unions remain available for
experiments; they are not how control letters are defined.
"""

from __future__ import annotations

from dataclasses import dataclass

from typekernel.geo.contour import reverse_contour, signed_area
from typekernel.geo.outline import Outline
from typekernel.geo.path_builder import PathBuilder
from typekernel.geo.path_helpers import KAPPA
from typekernel.parts.compose import ComposedGlyph, GlyphAssembler
from typekernel.parts.context import DesignContext
from typekernel.parts.primitives import bowl, tittle, vertical_stem

__all__ = [
    "NMetrics",
    "build_control_letter",
    "build_control_word",
    "build_h",
    "build_i",
    "build_n",
    "build_o",
    "build_u",
    "h_from_n",
    "n_metrics",
    "u_from_n",
]


@dataclass(frozen=True, slots=True)
class NMetrics:
    """Shared proportions for ``n`` / ``h`` / ``u`` (from :class:`DesignContext`)."""

    stem: float
    counter: float  # inner face to inner face
    x_height: float
    ascender: float
    overshoot: float
    crown_y: float  # outer arch peak (x-height + overshoot)
    leg_top: float  # where outer arch meets the right leg top
    join_y: float  # inner crotch / counter spring height
    kappa: float  # shoulder handle ratio


def n_metrics(ctx: DesignContext) -> NMetrics:
    """Derive ``n``-family metrics from family proportions."""
    stem = ctx.stem
    counter = ctx.x_height * (0.46 + 0.12 * ctx.aperture)
    # Slightly flatter shoulder when roundness is low (coding); rounder when soft.
    kappa = KAPPA * (0.92 + 0.28 * ctx.roundness)
    crown_y = ctx.x_height + ctx.overshoot
    # Outer meet: just under x-height so crown overshoots; inner join lower.
    leg_top = ctx.x_height - stem * 0.02
    join_y = ctx.x_height * (0.50 + 0.04 * ctx.roundness)
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
    )


def _pack(ctx: DesignContext, outline: Outline, *extra: Outline) -> ComposedGlyph:
    """Sidebearing pack; single outline — no boolean letter topology."""
    asm = GlyphAssembler(ctx).add(outline)
    for e in extra:
        asm.add(e)
    return asm.build()


def _n_family_outline(ctx: DesignContext, *, left_top: float, m: NMetrics) -> Outline:
    """One continuous CCW outer contour: left stem + shoulder + right leg.

    No third ``arch`` mesh and no ``union``. Inner counter is the hole formed
    by the single outline (stem insides + inner shoulder).
    """
    t = m.stem
    w = m.counter
    # x bands: left stem [0,t], counter (t, t+w), right leg [t+w, t+w+t]
    l0, l1 = 0.0, t
    r0, r1 = t + w, t + w + t
    mid = (l1 + r0) / 2.0
    k = m.kappa
    crown = m.crown_y
    leg_top = m.leg_top
    join = m.join_y

    # Outer shoulder cubics: (l1, left_top_connect) → crown → (r1, leg_top)
    # For n, left_top == x_height and we connect from top-right of left stem.
    # For h, left stem rises to ascender; arch still springs at x_height on the
    # right face of the left stem.
    spring_y = min(left_top, m.x_height)

    b = PathBuilder()
    # --- outer ---
    b.moveTo(l0, 0.0)
    b.lineTo(l0, left_top)
    b.lineTo(l1, left_top)
    if left_top > spring_y + 0.5:
        # h: down the right face of the ascender stem to the arch spring
        b.lineTo(l1, spring_y)
    # outer arch (two cubics, horizontal tangent at crown)
    b.curveTo(
        l1,
        spring_y + k * (crown - spring_y),
        mid - k * (mid - l1),
        crown,
        mid,
        crown,
    )
    b.curveTo(
        mid + k * (r1 - mid),
        crown,
        r1,
        leg_top + k * (crown - leg_top),
        r1,
        leg_top,
    )
    b.lineTo(r1, 0.0)
    b.lineTo(r0, 0.0)
    # --- inner right leg up to inner shoulder ---
    b.lineTo(r0, join)
    # inner arch (lower), right → left, horizontal at inner crown
    inner_crown = crown - t * (0.92 + 0.08 * ctx.contrast)
    # Keep inner crown below outer and above join
    inner_crown = min(inner_crown, crown - t * 0.75)
    inner_crown = max(inner_crown, join + t * 0.35)
    b.curveTo(
        r0,
        join + k * (inner_crown - join),
        mid + k * (r0 - mid),
        inner_crown,
        mid,
        inner_crown,
    )
    b.curveTo(
        mid - k * (mid - l1),
        inner_crown,
        l1,
        join + k * (inner_crown - join),
        l1,
        join,
    )
    b.lineTo(l1, 0.0)
    b.closePath()
    outline = b.build()
    # Font convention: outer contour CCW (positive signed area).
    c0 = outline.contours[0]
    if signed_area(c0) < 0:
        outline = Outline((reverse_contour(c0),))
    return outline


def build_n(ctx: DesignContext) -> ComposedGlyph:
    """Control ``n``: continuous cubic outline from family proportions."""
    m = n_metrics(ctx)
    return _pack(ctx, _n_family_outline(ctx, left_top=m.x_height, m=m))


def build_h(ctx: DesignContext) -> ComposedGlyph:
    """``h`` from the same shoulder/leg recipe as ``n`` (ascender left stem)."""
    m = n_metrics(ctx)
    return _pack(ctx, _n_family_outline(ctx, left_top=m.ascender, m=m))


def h_from_n(n_glyph: ComposedGlyph, ctx: DesignContext | None = None) -> ComposedGlyph:
    """Derive ``h`` from an ``n`` control glyph's context (shared metrics).

    Does not copy point data from ``n_glyph``; recomputes with the same
    :func:`n_metrics` so shoulder/leg match ``build_n`` for that context.
    Passing ``n_glyph`` documents the designer dependency chain for agents.
    """
    c = ctx if ctx is not None else n_glyph.context
    return build_h(c)


def build_o(ctx: DesignContext) -> ComposedGlyph:
    """Control ``o``: superellipse bowl (continuous cubics) + counter."""
    ry = ctx.x_height / 2.0 + ctx.overshoot
    rx = ry * (0.88 + 0.10 * ctx.aperture)
    # Squircle when roundness low (coding); ellipse when soft.
    n_exp = 2.0 + 0.7 * (1.0 - max(0.0, min(1.0, ctx.roundness)))
    outer, hole = bowl(
        ctx,
        rx,
        ctx.x_height / 2.0,
        rx=rx,
        ry=ry,
        thickness=ctx.stem,
        shape="superellipse",
        n=n_exp,
    )
    asm = GlyphAssembler(ctx).add(outer).add_hole(hole).subtract_holes()
    return asm.build()


def build_u(ctx: DesignContext) -> ComposedGlyph:
    """``u`` related to ``n``: mirrored trough logic (continuous outline)."""
    return u_from_n(build_n(ctx), ctx)


def u_from_n(n_glyph: ComposedGlyph, ctx: DesignContext | None = None) -> ComposedGlyph:
    """Derive ``u`` with the same counter/stem rhythm as control ``n``."""
    c = ctx if ctx is not None else n_glyph.context
    m = n_metrics(c)
    t = m.stem
    w = m.counter
    l0, l1 = 0.0, t
    r0, r1 = t + w, t + w + t
    mid = (l1 + r0) / 2.0
    k = m.kappa
    top = m.x_height
    # Bottom outer overshoots below baseline
    bottom = -m.overshoot
    inner_bottom = bottom + t * (0.92 + 0.08 * c.contrast)
    inner_bottom = max(inner_bottom, bottom + t * 0.7)

    b = PathBuilder()
    # outer: left down, bottom arch, right up
    b.moveTo(l0, top)
    b.lineTo(l0, m.join_y * 0.55 + t * 0.2)
    # use join-ish spring into bottom bowl
    spring = max(m.join_y * 0.35, t * 1.1)
    b.lineTo(l0, spring)
    b.curveTo(
        l0,
        spring - k * (spring - bottom),
        mid - k * (mid - l0),
        bottom,
        mid,
        bottom,
    )
    b.curveTo(
        mid + k * (r1 - mid),
        bottom,
        r1,
        spring - k * (spring - bottom),
        r1,
        spring,
    )
    b.lineTo(r1, top)
    b.lineTo(r0, top)
    b.lineTo(r0, spring)
    b.curveTo(
        r0,
        spring - k * (spring - inner_bottom),
        mid + k * (r0 - mid),
        inner_bottom,
        mid,
        inner_bottom,
    )
    b.curveTo(
        mid - k * (mid - l1),
        inner_bottom,
        l1,
        spring - k * (spring - inner_bottom),
        l1,
        spring,
    )
    b.lineTo(l1, top)
    b.closePath()
    return _pack(c, b.build())


def build_i(ctx: DesignContext) -> ComposedGlyph:
    """Simple ``i``: flat stem + tittle (not a control glyph; specimen helper)."""
    stem = vertical_stem(ctx, 0.0, 0.0, ctx.x_height)
    dot = tittle(ctx, ctx.stem / 2.0, ctx.x_height + ctx.stem * 0.55)
    return GlyphAssembler(ctx).add(stem).add(dot).build()


CONTROL_BUILDERS = {
    "n": build_n,
    "h": build_h,
    "o": build_o,
    "u": build_u,
    "i": build_i,
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
