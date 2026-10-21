"""Assemble a :class:`~typekernel.font.Font` from already-derived glyphs (Usage A).

Wires spacing, kerning, and OpenType feature text so referenced glyphs always
exist. Agents compose parts → glyph map, then call :func:`compose_font`.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from typekernel.compile.features import (
    add_case_punctuation,
    add_fraction_forms,
    add_ordn_forms,
    add_standard_ligatures,
    add_tabular_alternates,
    standard_feature_text,
)
from typekernel.font import Font
from typekernel.optics.glyph_polish import GlyphPolishOptions, polish_glyph_map
from typekernel.optics.joins import JoinPolicy
from typekernel.optics.space import space_font
from typekernel.parts.compose import ComposedGlyph
from typekernel.parts.context import DesignContext
from typekernel.parts.diacritics import add_composite_latin
from typekernel.parts.metrics import (
    KernClass,
    auto_class_kern,
    auto_side_kern_classes,
    fit_glyph_pair_kerns,
    rhythm_from_control_glyphs,
)

__all__ = [
    "DEFAULT_PAIR_KERN_EXCEPTIONS",
    "FamilyBuildOptions",
    "compose_font",
    "reference_kern_classes",
]


# Class reps miss these diagonal/round pairs; optical fit closes the gap.
DEFAULT_PAIR_KERN_EXCEPTIONS: tuple[tuple[str, str], ...] = (
    ("o", "w"),
    ("a", "v"),
    ("T", "a"),
    ("L", "T"),
)


@dataclass(frozen=True, slots=True)
class FamilyBuildOptions:
    """OpenType and charset knobs aligned with shipped glyphs."""

    liga: bool = False
    tnum: bool = False
    case: bool = False
    frac: bool = False
    ordn: bool = False
    extended_latin: str = ""
    space_width_factor: float = 0.45
    pair_kern_exceptions: tuple[tuple[str, str], ...] = DEFAULT_PAIR_KERN_EXCEPTIONS
    joins_policy: JoinPolicy = "tangent_fix"
    ease_curvature: bool = False

    def polish_options(self) -> GlyphPolishOptions:
        return GlyphPolishOptions(
            joins_policy=self.joins_policy,
            ease_curvature=self.ease_curvature,
        )

    def feature_text(self) -> str:
        return standard_feature_text(
            tnum=self.tnum, liga=self.liga, case=self.case,
            frac=self.frac, ordn=self.ordn,
        )


def reference_kern_classes(
    glyphs: Mapping[str, ComposedGlyph],
    ctx: DesignContext,
    *,
    options: FamilyBuildOptions | None = None,
) -> tuple[KernClass, ...]:
    """Kern classes from a derived glyph map (reuse for VF masters)."""
    opts = options or FamilyBuildOptions()
    drawn = polish_glyph_map(dict(glyphs), opts.polish_options())
    rhythm = rhythm_from_control_glyphs(drawn["n"], drawn["o"])
    spaced = space_font(drawn, ctx, rhythm=rhythm)
    return auto_side_kern_classes(spaced, ctx)


def compose_font(
    glyphs: Mapping[str, ComposedGlyph],
    ctx: DesignContext,
    family: str,
    style: str = "Regular",
    *,
    weight_class: int = 400,
    options: FamilyBuildOptions | None = None,
    kern_classes: Sequence[KernClass] | None = None,
    control_pair: tuple[ComposedGlyph, ComposedGlyph] | None = None,
) -> Font:
    """Design-time font: spaced glyphs, class kern, feature-safe defaults.

    ``glyphs`` must already include every character you want shipped (Usage A
    composition or :meth:`~typekernel.parts.family.FormSources.derive`).
    """
    opts = options or FamilyBuildOptions()
    drawn = polish_glyph_map(dict(glyphs), opts.polish_options())
    if "n" not in drawn or "o" not in drawn:
        raise KeyError("compose_font requires glyphs for both 'n' and 'o'")
    rhythm = rhythm_from_control_glyphs(drawn["n"], drawn["o"])
    spaced = space_font(drawn, ctx, rhythm=rhythm)
    classes = (
        tuple(kern_classes)
        if kern_classes is not None
        else auto_side_kern_classes(spaced, ctx)
    )
    kerning = auto_class_kern(spaced, classes, target=rhythm)

    font = Font.from_context(
        ctx,
        family,
        style,
        weight_class=weight_class,
        space_width=spaced["n"].advance * opts.space_width_factor,
    )
    font.add_chars(spaced)
    pair = control_pair or (drawn["n"], drawn["o"])
    if opts.extended_latin:
        add_composite_latin(font, pair)
    if opts.tnum:
        add_tabular_alternates(font, spaced)
    if opts.liga:
        add_standard_ligatures(font, pair)
    if opts.case:
        add_case_punctuation(font, spaced)
    if opts.frac:
        add_fraction_forms(
            font,
            {ch: spaced[ch] for ch in "0123456789" if ch in spaced},
            slash=spaced.get("/"),
        )
    if opts.ordn:
        add_ordn_forms(font, spaced)
    font.features = opts.feature_text()
    font.add_class_kern_table(kerning)
    if opts.pair_kern_exceptions:
        font.add_kern_table(
            fit_glyph_pair_kerns(spaced, opts.pair_kern_exceptions, target=rhythm)
        )
    return font
