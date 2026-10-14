"""Optical primitives for typekernel.

These operators adjust designed outlines for perception (overshoot, stem
measure, join cleanup, contrast targets, optical spacing). They are **not**
stroke expansion and must never be implemented as pen-radius weight.
"""

from __future__ import annotations

from typekernel.optics.context import OpticalContext
from typekernel.optics.contrast import (
    ContrastParams,
    apply_designed_contrast,
    validate_contrast_params,
)
from typekernel.optics.glyph_polish import GlyphPolishOptions, polish_glyph, polish_glyph_map
from typekernel.optics.joins import cleanup_joins
from typekernel.optics.overshoot import apply_overshoot
from typekernel.optics.pipeline import apply
from typekernel.optics.sidebearing import suggest_sidebearings
from typekernel.optics.space import (
    OpticalSpacingResult,
    fit_kern_pair,
    measure_side_whitespace,
    pair_gap_bbox,
    pair_gap_optical,
    space_font,
    space_word_optical,
    suggest_sidebearings_optical,
    with_sidebearings,
)
from typekernel.optics.stem import (
    HorizontalStemSpan,
    StemContrastReport,
    VerticalStemSpan,
    diagonal_compensation,
    equalize_horizontal_stems,
    equalize_vertical_stems,
    horizontal_vs_vertical_report,
    list_horizontal_stems,
    list_vertical_stems,
    measure_horizontal_stem,
    measure_oriented_stem,
    measure_vertical_stem,
)

__all__ = [
    "ContrastParams",
    "GlyphPolishOptions",
    "HorizontalStemSpan",
    "OpticalContext",
    "OpticalSpacingResult",
    "StemContrastReport",
    "VerticalStemSpan",
    "apply",
    "apply_designed_contrast",
    "apply_overshoot",
    "cleanup_joins",
    "diagonal_compensation",
    "equalize_horizontal_stems",
    "equalize_vertical_stems",
    "fit_kern_pair",
    "horizontal_vs_vertical_report",
    "list_horizontal_stems",
    "list_vertical_stems",
    "measure_horizontal_stem",
    "measure_oriented_stem",
    "measure_side_whitespace",
    "measure_vertical_stem",
    "pair_gap_bbox",
    "pair_gap_optical",
    "polish_glyph",
    "polish_glyph_map",
    "space_font",
    "space_word_optical",
    "suggest_sidebearings",
    "suggest_sidebearings_optical",
    "validate_contrast_params",
    "with_sidebearings",
]
