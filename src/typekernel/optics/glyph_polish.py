"""Polish composed glyph outlines before spacing and export."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, replace

from typekernel.optics.joins import JoinPolicy, cleanup_joins
from typekernel.parts.compose import ComposedGlyph

__all__ = [
    "GlyphPolishOptions",
    "polish_glyph",
    "polish_glyph_map",
]


@dataclass(frozen=True, slots=True)
class GlyphPolishOptions:
    """Join cleanup applied uniformly across a family draw."""

    joins_policy: JoinPolicy = "tangent_fix"
    ease_curvature: bool = False
    tangent_radius: float | None = None
    kink_max_deg: float = 30.0

    @classmethod
    def noop(cls) -> GlyphPolishOptions:
        return cls(joins_policy="noop")


def _polish_outline(outline, opts: GlyphPolishOptions):
    from typekernel.geo.joins import ease_curvature

    if opts.joins_policy == "noop":
        return outline
    out = cleanup_joins(
        outline,
        policy=opts.joins_policy,
        radius=opts.tangent_radius,
        kink_max_deg=opts.kink_max_deg,
    )
    if opts.ease_curvature:
        out = ease_curvature(out, angle_tol=0.5, min_handle=1.0, both_ends=True)
    return out


def polish_glyph(glyph: ComposedGlyph, options: GlyphPolishOptions | None = None) -> ComposedGlyph:
    """Return a copy with cleaned solid outlines (holes unchanged)."""
    opts = options or GlyphPolishOptions()
    if opts.joins_policy == "noop" and not opts.ease_curvature:
        return glyph
    solids = tuple(_polish_outline(o, opts) for o in glyph.solids)
    holes = (
        tuple(_polish_outline(h, opts) for h in glyph.holes)
        if opts.ease_curvature
        else glyph.holes
    )
    return replace(glyph, solids=solids, holes=holes)


def polish_glyph_map(
    glyphs: Mapping[str, ComposedGlyph],
    options: GlyphPolishOptions | None = None,
) -> dict[str, ComposedGlyph]:
    """Polish every entry (typical post-:meth:`~typekernel.parts.family.Controls.build_all`)."""
    opts = options or GlyphPolishOptions()
    if opts.joins_policy == "noop" and not opts.ease_curvature:
        return dict(glyphs)
    return {name: polish_glyph(g, opts) for name, g in glyphs.items()}
