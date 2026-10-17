"""Assemble a :class:`~typekernel.font.Font` from a control sheet (agent path).

Wires spacing, kerning, and OpenType feature text so referenced glyphs always
exist. Prefer this over hand-rolling ``Font`` + ``standard_feature_text``.
"""

from __future__ import annotations

from collections.abc import Sequence
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
from typekernel.parts.diacritics import add_composite_latin
from typekernel.parts.family import Controls
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
    "compose_font_from_controls",
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
    chars: str | None = None
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


def _compose_charset(controls: Controls, opts: FamilyBuildOptions) -> str:
    """Charset that ``build_all`` will derive for this compose call."""
    if opts.chars is not None:
        return "".join(dict.fromkeys(opts.chars + "no"))
    if opts.extended_latin:
        return controls.supported + opts.extended_latin
    return controls.supported


def reference_kern_classes(
    controls: Controls,
    *,
    require_body_unlock: bool = True,
) -> tuple[KernClass, ...]:
    """Kern classes from the regular control draw (reuse for VF masters).

    Defaults to the same charset DesignSequence unlock as
    :func:`compose_font_from_controls` (body / caps / digits as present).
    Pass ``require_body_unlock=False`` only for documented stock / specimen
    compiles.
    """
    from typekernel.qa.design_sequence import ensure_controls_unlocked_for_charset

    charset = controls.supported if controls.supported else ""
    ensure_controls_unlocked_for_charset(
        controls, charset, require=require_body_unlock
    )
    ctx = controls.context
    opts = FamilyBuildOptions()
    drawn = polish_glyph_map(
        controls.build_all(charset if charset else None),
        opts.polish_options(),
    )
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
    require_body_unlock: bool = True,
) -> Font:
    """Design-time font: spaced glyphs, class kern, feature-safe defaults.

    By default runs DesignSequence unlocks for every subset present in the
    compose charset (body, caps, digits) before ``build_all``, so agents cannot
    ship ungated capitals or figures after only unlocking lowercase. Pass
    ``require_body_unlock=False`` only for already-validated stock compile
    paths (unit tests of features / polish), never as a design method.
    """
    opts = options or FamilyBuildOptions()
    charset = _compose_charset(controls, opts)
    if require_body_unlock:
        from typekernel.qa.design_sequence import (
            DesignSequenceError,
            ensure_controls_unlocked_for_charset,
        )

        try:
            ensure_controls_unlocked_for_charset(controls, charset, require=True)
        except DesignSequenceError as exc:
            raise DesignSequenceError(
                "compose_font_from_controls requires DesignSequence unlock "
                "(body / caps / digits as present in charset) before compile — "
                "redesign refused glyphs, then retry (or unlock via "
                f"Controls.unlock_body / unlock_caps / unlock_digits). {exc}"
            ) from exc
    ctx = controls.context
    drawn = polish_glyph_map(controls.build_all(charset), opts.polish_options())
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
