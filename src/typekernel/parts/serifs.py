"""Stem serif attachment (TK-306): slab and bracketed feet/caps from stem anchors."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Literal

from typekernel.geo.boolean import union_all
from typekernel.geo.outline import Outline
from typekernel.geo.path_builder import PathBuilder
from typekernel.geo.path_helpers import KAPPA
from typekernel.parts.compose import ComposedGlyph, GlyphAssembler
from typekernel.parts.context import DesignContext
from typekernel.parts.primitives import rounded_rect, serif_bracket

__all__ = [
    "StemSerifSite",
    "apply_glyph_serifs",
    "bracketed_stem_foot_dims",
    "inline_hook_cap_serif_path",
    "inline_shoulder_left_cap_slab_path",
    "inline_stem_cap_serif_path",
    "inline_stem_cap_serif_path_slab_rect",
    "inline_stem_foot_serif_path",
    "inline_stem_foot_serif_path_right",
    "serif_metrics",
    "slab_serif_rect",
]

_STEM_ANCHOR = re.compile(r"^stem_([LMR])_([bt])$")


@dataclass(frozen=True, slots=True)
class StemSerifSite:
    """One foot or cap on a vertical stem face."""

    side: Literal["L", "M", "R"]
    edge: Literal["b", "t"]
    center_x: float
    y: float
    stem_width: float


def serif_metrics(ctx: DesignContext) -> tuple[float, float, float]:
    """Return ``(length, thickness, bracket_radius)`` in design units."""
    length = ctx.stem * 0.62
    thickness = max(ctx.thin * 0.92, ctx.stem * 0.14)
    bracket = min(ctx.join_radius * 0.55, thickness * 0.85, length * 0.35)
    return length, thickness, bracket


def slab_serif_rect(
    ctx: DesignContext,
    site: StemSerifSite,
    *,
    length: float | None = None,
    thickness: float | None = None,
) -> Outline:
    """Axis-aligned slab serif centered on ``site.center_x``."""
    default_len, default_th, _ = serif_metrics(ctx)
    length = default_len if length is None else length
    thickness = default_th if thickness is None else thickness
    half_stem = site.stem_width / 2.0
    x0 = site.center_x - half_stem - length
    x1 = site.center_x + half_stem + length
    if site.edge == "b":
        y0, y1 = site.y - thickness, site.y
    else:
        y0, y1 = site.y, site.y + thickness
    return rounded_rect(ctx, x0, y0, x1, y1, radius=min(ctx.join_radius * 0.25, thickness * 0.2))


def _bracket_serif(
    ctx: DesignContext,
    site: StemSerifSite,
    *,
    length: float | None = None,
    thickness: float | None = None,
) -> Outline:
    length_d, thick_d, _ = serif_metrics(ctx)
    length = length_d if length is None else length
    thickness = thick_d if thickness is None else thickness
    if site.side == "L":
        x_stem = site.center_x + site.stem_width / 2.0
        side = "left"
    elif site.side == "R":
        x_stem = site.center_x - site.stem_width / 2.0
        side = "right"
    else:
        x_stem = site.center_x - site.stem_width / 2.0
        side = "right"
    if site.edge == "b":
        y_base = site.y - thickness
    else:
        y_base = site.y
    return serif_bracket(
        ctx, x_stem, y_base, side=side, length=length, thickness=thickness
    )


def _stem_width(glyph: ComposedGlyph) -> float:
    design = glyph.design
    if design is not None and hasattr(design, "stem"):
        return float(design.stem)
    return glyph.context.stem


def _sites_from_anchors(glyph: ComposedGlyph) -> list[StemSerifSite]:
    width = _stem_width(glyph)
    sites: list[StemSerifSite] = []
    for anchor in glyph.anchors:
        m = _STEM_ANCHOR.match(anchor.name)
        if m is None:
            continue
        side, edge = m.group(1), m.group(2)
        sites.append(
            StemSerifSite(
                side=side,  # type: ignore[arg-type]
                edge=edge,  # type: ignore[arg-type]
                center_x=anchor.x,
                y=anchor.y,
                stem_width=width,
            )
        )
    return sites


def bracketed_stem_foot_dims(
    ctx: DesignContext,
    stem_width: float,
    y_base: float,
) -> tuple[float, float]:
    """Foot serif length and thickness for inline bracketed stems (bowls, hooks)."""
    from typekernel.parts.weight_relief import stem_weight_fraction

    length, thick, _ = serif_metrics(ctx)
    heavy = stem_weight_fraction(stem_width)
    l = min(length, stem_width * 0.48) * (1.0 - 0.22 * heavy)
    th = min(thick, ctx.x_height * 0.1, stem_width * 0.18) * (1.0 - 0.18 * heavy)
    if y_base < 0.0:
        # Descender bowl feet: short bracket so the foot does not re-enter the bowl.
        l = min(l, stem_width * (0.34 - 0.08 * heavy))
        th = min(th, ctx.x_height * (0.055 - 0.012 * heavy), abs(y_base) * 0.09)
    return l, th


def _bracket_fillet_at_outer_corner(
    b: PathBuilder,
    *,
    x_corner: float,
    y_horiz: float,
    y_vert_end: float,
    x_from: float,
    bracket_r: float,
) -> None:
    """Fillet the outer corner between a horizontal and a vertical segment."""
    span_x = abs(x_from - x_corner)
    span_y = abs(y_vert_end - y_horiz)
    if span_x <= 0 or span_y <= 0:
        raise ValueError("corner spans must be positive")
    r = min(bracket_r, span_x * 0.4, span_y * 0.45)
    if r < 0.35:
        b.lineTo(x_corner, y_horiz)
        b.lineTo(x_corner, y_vert_end)
        return
    b.lineTo(x_corner + r, y_horiz)
    b.curveTo(
        x_corner + r - r * KAPPA,
        y_horiz,
        x_corner,
        y_horiz + r - r * KAPPA,
        x_corner,
        y_horiz + r,
    )
    b.lineTo(x_corner, y_vert_end)


def inline_stem_foot_serif_path(
    b: PathBuilder,
    x_stem_left: float,
    y_base: float,
    ctx: DesignContext,
    stem_width: float,
) -> None:
    """Append a foot serif on the left face of a vertical stem (fixed segment count)."""
    l, th = bracketed_stem_foot_dims(ctx, stem_width, y_base)
    _, _, bracket_r = serif_metrics(ctx)
    xl = x_stem_left - l
    yt = y_base - th
    b.lineTo(x_stem_left, yt)
    _bracket_fillet_at_outer_corner(
        b,
        x_corner=xl,
        y_horiz=yt,
        y_vert_end=y_base,
        x_from=x_stem_left,
        bracket_r=bracket_r,
    )
    b.lineTo(x_stem_left, y_base)


def inline_stem_foot_serif_path_right(
    b: PathBuilder,
    x_stem_right: float,
    y_base: float,
    ctx: DesignContext,
    stem_width: float,
) -> None:
    """Append a foot serif on the right face of a vertical stem (fixed segment count)."""
    l, th = bracketed_stem_foot_dims(ctx, stem_width, y_base)
    _, _, bracket_r = serif_metrics(ctx)
    xr = x_stem_right + l
    yt = y_base - th
    b.lineTo(x_stem_right, yt)
    _bracket_fillet_at_outer_corner(
        b,
        x_corner=xr,
        y_horiz=yt,
        y_vert_end=y_base,
        x_from=x_stem_right,
        bracket_r=bracket_r,
    )
    b.lineTo(x_stem_right, y_base)


def inline_shoulder_left_cap_slab_path(
    b: PathBuilder,
    x_stem_left: float,
    y_cap: float,
    ctx: DesignContext,
    stem_width: float,
) -> None:
    """Slab cap on the left face only; current point ``(x_stem_left, y_cap)``."""
    length, thick, _ = serif_metrics(ctx)
    l = min(length, stem_width * 0.5)
    th = min(thick, y_cap * 0.1, stem_width * 0.2)
    xl = x_stem_left - l
    b.lineTo(xl, y_cap)
    b.lineTo(xl, y_cap + th)
    b.lineTo(x_stem_left, y_cap + th)
    b.lineTo(x_stem_left, y_cap)


def inline_stem_cap_serif_path_slab_rect(
    b: PathBuilder,
    x_stem_left: float,
    x_stem_right: float,
    y_cap: float,
    ctx: DesignContext,
    stem_width: float,
    *,
    thickness_scale: float = 1.0,
) -> None:
    """Full-width slab rectangle cap; current point ``(x_stem_right, y_cap)``."""
    length, thick, _ = serif_metrics(ctx)
    l = min(length, stem_width * 0.5)
    th = min(thick, y_cap * 0.1, stem_width * 0.2) * thickness_scale
    xl = x_stem_left - l
    b.lineTo(xl, y_cap)
    b.lineTo(xl, y_cap + th)
    b.lineTo(x_stem_right, y_cap + th)
    b.lineTo(x_stem_right, y_cap)


def inline_stem_cap_serif_path(
    b: PathBuilder,
    x_stem_left: float,
    x_stem_right: float,
    y_cap: float,
    ctx: DesignContext,
    stem_width: float,
) -> None:
    """Left-stem cap serif; current point must be ``(x_stem_right, y_cap)``."""
    from typekernel.parts.caps import HMetrics, _append_upward_cap_foot_pad, _i_cap_foot_dims

    h = HMetrics(
        stem=stem_width,
        bar=stem_width * ctx.contrast * 0.92,
        cap_height=y_cap,
        width=stem_width,
        bar_y=y_cap * 0.52,
        overshoot=0.0,
    )
    l, th, bracket_r = _i_cap_foot_dims(h, ctx)
    if ctx.style.serif == "slab":
        inline_stem_cap_serif_path_slab_rect(
            b, x_stem_left, x_stem_right, y_cap, ctx, stem_width
        )
        return
    _append_upward_cap_foot_pad(
        b,
        x_stem_left - l,
        x_stem_right,
        y_cap,
        th,
        bracket_r,
        bracketed=True,
    )
    b.lineTo(x_stem_right, y_cap)


def inline_hook_cap_serif_path(
    b: PathBuilder,
    x_stem_left: float,
    x_stem_right: float,
    y_base: float,
    foot_l: float,
    foot_th: float,
    bracket_r: float,
) -> None:
    """Cap serif on a hook stem (left face at ``x_stem_left``), fixed segment count."""
    xl = x_stem_left - foot_l
    yt = y_base + foot_th
    _bracket_fillet_at_outer_corner(
        b,
        x_corner=xl,
        y_horiz=y_base,
        y_vert_end=yt,
        x_from=x_stem_left,
        bracket_r=bracket_r,
    )
    b.lineTo(x_stem_right, yt)
    b.lineTo(x_stem_right, y_base)


def _serif_outline(ctx: DesignContext, site: StemSerifSite) -> Outline:
    if ctx.style.serif == "bracketed":
        return _bracket_serif(ctx, site)
    return slab_serif_rect(ctx, site)


def apply_glyph_serifs(glyph: ComposedGlyph) -> ComposedGlyph:
    """Union stem serifs when ``ctx.style.serif`` is not ``none``."""
    ctx = glyph.context
    if ctx.style.serif == "none":
        return glyph
    sites = _sites_from_anchors(glyph)
    if not sites:
        return glyph
    serif_parts = [_serif_outline(ctx, site) for site in sites]
    ink = list(glyph.solids)
    if ink:
        stem = ink[0]
        merged = (
            union_all([stem, *serif_parts])
            if serif_parts
            else stem
        )
        ink = [merged, *ink[1:]]
    asm = GlyphAssembler(ctx).with_design(glyph.design)
    for solid in ink:
        asm.add(solid)
    for hole in glyph.holes:
        asm.add_hole(hole)
    for anchor in glyph.anchors:
        asm.anchor(anchor.name, anchor.x, anchor.y)
    return asm.build()
