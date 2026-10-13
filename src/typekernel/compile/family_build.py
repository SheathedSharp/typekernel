"""Assemble a :class:`~typekernel.font.Font` from a control sheet (agent path).

Wires spacing, kerning, and OpenType feature text so referenced glyphs always
exist. Prefer this over hand-rolling ``Font`` + ``standard_feature_text``.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from typekernel.compile.features import (
    add_case_punctuation,
    add_standard_ligatures,
    add_tabular_alternates,
    standard_feature_text,
)
from typekernel.parts.diacritics import add_composite_latin
from typekernel.font import Font
from typekernel.optics.space import space_font
from typekernel.parts.family import Controls
from typekernel.parts.metrics import (
    KernClass,
    auto_class_kern,
    auto_side_kern_classes,
    rhythm_from_control_glyphs,
)

__all__ = [
    "FamilyBuildOptions",
    "compose_font_from_controls",
    "reference_kern_classes",
]


@dataclass(frozen=True, slots=True)
class FamilyBuildOptions:
    """OpenType and charset knobs aligned with shipped glyphs."""

    liga: bool = False
    tnum: bool = False
    case: bool = False
    extended_latin: str = ""
    chars: str | None = None
    space_width_factor: float = 0.45

    def feature_text(self) -> str:
        return standard_feature_text(tnum=self.tnum, liga=self.liga, case=self.case)


def reference_kern_classes(controls: Controls) -> tuple[KernClass, ...]:
    """Kern classes from the regular control draw (reuse for VF masters)."""
    ctx = controls.context
    drawn = controls.build_all(controls.supported if controls.supported else None)
    rhythm = rhythm_from_control_glyphs(drawn["n"], drawn["o"])
    spaced = space_font(drawn, ctx, rhythm=rhythm)
    return auto_side_kern_classes(spaced, ctx)


def compose_font_from_controls(
    controls: Controls,
    family: str,
    style: str = "Regular",
    *,
    weight_class: int = 400,
    options: FamilyBuildOptions | None = None,
    kern_classes: Sequence[KernClass] | None = None,
) -> Font:
    """Design-time font: spaced glyphs, class kern, feature-safe defaults."""
    opts = options or FamilyBuildOptions()
    ctx = controls.context
    if opts.chars is not None:
        charset: str | None = opts.chars
    elif opts.extended_latin:
        charset = controls.supported + opts.extended_latin
    else:
        charset = None
    drawn = controls.build_all(charset)
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
    if opts.extended_latin:
        add_composite_latin(font, controls.control_glyphs())
    if opts.tnum:
        add_tabular_alternates(font, spaced)
    if opts.liga:
        add_standard_ligatures(font, controls.control_glyphs())
    if opts.case:
        add_case_punctuation(font, spaced)
    font.features = opts.feature_text()
    font.add_class_kern_table(kerning)
    return font
