"""Stem serif attachment (TK-306): slab and bracketed feet/caps from stem anchors."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Literal

from typekernel.geo.boolean import union_all
from typekernel.geo.outline import Outline
from typekernel.parts.compose import ComposedGlyph, GlyphAssembler
from typekernel.parts.context import DesignContext
from typekernel.parts.primitives import rounded_rect, serif_bracket

__all__ = [
    "StemSerifSite",
    "apply_glyph_serifs",
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
    y = site.y if site.edge == "b" else site.y - thickness
    return serif_bracket(ctx, x_stem, y, side=side, length=length, thickness=thickness)


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
