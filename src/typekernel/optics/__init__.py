"""Optical primitives for typekernel."""

from __future__ import annotations

from typekernel.optics.context import OpticalContext
from typekernel.optics.contrast import (
    ContrastParams,
    apply_designed_contrast,
    validate_contrast_params,
)
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
    vertical_equiv_from_diagonal,
)

__all__ = [
    "ContrastParams",
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
    "space_font",
    "space_word_optical",
    "suggest_sidebearings",
    "suggest_sidebearings_optical",
    "validate_contrast_params",
    "vertical_equiv_from_diagonal",
    "with_sidebearings",
]
