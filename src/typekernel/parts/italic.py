"""Italic masters: metric tweak plus construct-time stem slant (M4a).

``italic_design`` builds a separate control sheet whose glyphs are drawn with
``DesignContext.italic_slant_deg`` applied at compose time (same point-count as
the regular master for interpolation). Branching arches and other true-italic
topology (M4 TK-403) are not implemented yet.

For mechanical oblique on a finished font, use
:func:`~typekernel.compile.oblique.oblique_font` — do not label that as Italic.
"""

from __future__ import annotations

from dataclasses import dataclass, replace

from typekernel.axes.slant import ObliqueTransform
from typekernel.parts.compose import Anchor, ComposedGlyph
from typekernel.parts.family import Controls

__all__ = [
    "ItalicStyle",
    "italic_controls",
    "italic_design",
    "slant_composed_glyph",
]


@dataclass(frozen=True, slots=True)
class ItalicStyle:
    """Knobs for an italic control sheet derived from a regular sheet."""

    slant_deg: float = 10.0
    lean: float = 1.035
    contrast_scale: float = 0.96


def italic_design(regular: Controls, *, style: ItalicStyle | None = None) -> Controls:
    """Return an italic master: wider counters + construct slant on every glyph."""
    s = style or ItalicStyle()
    ctx = regular.context.tuned(
        contrast=max(0.88, regular.context.contrast * s.contrast_scale),
        italic_slant_deg=s.slant_deg,
    )
    n = regular.n.tuned(counter=regular.n.counter * s.lean)
    o = regular.o.tuned(
        rx=regular.o.rx * s.lean,
        ry=regular.o.ry * (s.lean * 0.98),
    )
    return replace(regular, context=ctx, n=n, o=o)


def italic_controls(regular: Controls, *, lean: float = 1.035) -> Controls:
    """Deprecated name for :func:`italic_design` (kept for examples and VF demos)."""
    return italic_design(regular, style=ItalicStyle(lean=lean))


def slant_composed_glyph(glyph: ComposedGlyph, angle_deg: float) -> ComposedGlyph:
    """Apply construct slant to every solid and counter (topology preserved)."""
    if abs(angle_deg) < 1e-9:
        return glyph
    transform = ObliqueTransform(angle_deg)
    import math

    shear = math.tan(math.radians(angle_deg))

    def shift_anchor(anchor: Anchor) -> Anchor:
        return Anchor(anchor.name, anchor.x + anchor.y * shear, anchor.y)

    solids = tuple(transform.apply(solid) for solid in glyph.solids)
    holes = tuple(transform.apply(hole) for hole in glyph.holes)
    return ComposedGlyph(
        solids,
        holes,
        glyph.advance,
        glyph.context,
        anchors=tuple(shift_anchor(a) for a in glyph.anchors),
        design=glyph.design,
    )
