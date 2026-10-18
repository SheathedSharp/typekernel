"""Italic masters: metric tweak plus construct-time stem slant (M4a).

``italic_design`` builds a separate control sheet whose glyphs are drawn with
``DesignContext.italic_slant_deg`` applied at compose time. Branching arches
for ``n`` / ``h`` / ``r`` / ``u`` / ``m`` when ``italic_slant_deg`` ≥ 6°
(TK-403). Upright masters in a ``wght×ital`` VF should use
:func:`vf_upright_controls` so segment counts match the italic master.

For mechanical oblique on a finished font, use
:func:`~typekernel.compile.oblique.oblique_font` — do not label that as Italic.

Agent gate: :func:`~typekernel.qa.design_sequence.unlock_controls_italic_body`
unlocks the Latin body on this sheet (construct slant + branching skips).
Diagonals ``k``/``v``/``w``/``x``/``y``/``z`` use cursive-cubic / asymmetric
italic constructions (topology differs from shear). Non-diagonal branching: left-stem ``n``/``h``/``m``/``r`` use construction
fillets; mirrored ``u`` uses ``_soften_italic_branch_crotch`` (emit is unsafe on
mirrored shoulders under weight relief). Sans stems get shared written
``_emit_italic_entry_kick`` / ``_emit_italic_exit_outstroke`` (and ``r`` a soft
arm terminal); VF-compat upright shares the same segment recipe.
"""

from __future__ import annotations

import math
import warnings
from dataclasses import dataclass, replace

from typekernel.axes.slant import ObliqueTransform
from typekernel.geo.layout import union_bounds
from typekernel.parts.compose import Anchor, ComposedGlyph
from typekernel.parts.family import Controls
from typekernel.parts.slant_compensate import horizontal_slant_compensation
from typekernel.parts.transforms import translate

__all__ = [
    "ItalicStyle",
    "horizontal_slant_compensation",
    "italic_controls",
    "italic_design",
    "slant_composed_glyph",
    "vf_italic_pair",
    "vf_upright_controls",
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
        vf_compat_stem_segments=False,
        sidebearing_ratio=min(
            0.18,
            regular.context.sidebearing_ratio * 1.12,
        ),
    )
    n = regular.n.tuned(counter=regular.n.counter * s.lean)
    o = regular.o.tuned(
        rx=regular.o.rx * s.lean,
        ry=regular.o.ry * (s.lean * 0.98),
    )
    return replace(regular, context=ctx, n=n, o=o)


def italic_controls(regular: Controls, *, lean: float = 1.035) -> Controls:
    """Deprecated name for :func:`italic_design` (kept for examples and VF demos)."""
    warnings.warn(
        "italic_controls() is deprecated; use italic_design(regular, style=ItalicStyle(...))",
        DeprecationWarning,
        stacklevel=2,
    )
    return italic_design(regular, style=ItalicStyle(lean=lean))


def vf_upright_controls(regular: Controls, *, oblique_split_deg: float = 10.0) -> Controls:
    """Upright sheet for ``wght×ital`` VFs (TK-404 segment compatibility)."""
    return replace(
        regular,
        context=regular.context.tuned(
            vf_compat_stem_segments=True,
            vf_compat_oblique_splits=True,
            vf_oblique_split_deg=oblique_split_deg,
        ),
    )


def vf_italic_pair(
    regular: Controls,
    *,
    style: ItalicStyle | None = None,
) -> tuple[Controls, Controls]:
    """Upright + italic sheets with matched oblique pre-split angle (TK-404)."""
    s = style or ItalicStyle()
    upright = vf_upright_controls(regular, oblique_split_deg=s.slant_deg)
    return upright, italic_design(upright, style=s)


def slant_composed_glyph(glyph: ComposedGlyph, angle_deg: float) -> ComposedGlyph:
    """Apply construct slant to every solid and counter (topology preserved)."""
    if abs(angle_deg) < 1e-9:
        return glyph
    transform = ObliqueTransform(angle_deg)

    shear = math.tan(math.radians(angle_deg))

    solids = tuple(transform.apply(solid) for solid in glyph.solids)
    holes = tuple(transform.apply(hole) for hole in glyph.holes)
    ctx = glyph.context
    x0, _, x1, _ = union_bounds([*solids, *holes])
    sb = max(0.025 * ctx.units_per_em, ctx.sidebearing_ratio * ctx.x_height)
    dx = sb - x0
    if abs(dx) > 1e-9:
        solids = tuple(translate(solid, dx, 0.0) for solid in solids)
        holes = tuple(translate(hole, dx, 0.0) for hole in holes)
    x0, _, x1, _ = union_bounds([*solids, *holes])
    advance = sb + (x1 - x0) + sb

    def place_anchor(anchor: Anchor) -> Anchor:
        return Anchor(anchor.name, anchor.x + anchor.y * shear + dx, anchor.y)

    return ComposedGlyph(
        solids,
        holes,
        advance,
        ctx,
        anchors=tuple(place_anchor(a) for a in glyph.anchors),
        design=glyph.design,
    )
