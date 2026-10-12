"""Optical primitives for typekernel.

These operators adjust designed outlines for perception (overshoot, stem
measure, join cleanup, contrast targets, optical spacing). They are **not**
stroke expansion and must never be implemented as pen-radius weight.
"""

from __future__ import annotations

from typekernel.optics.context import OpticalContext
from typekernel.optics.contrast import ContrastParams, validate_contrast_params
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
    space_word_optical,
    suggest_sidebearings_optical,
    with_sidebearings,
)
from typekernel.optics.stem import equalize_vertical_stems, measure_vertical_stem

__all__ = [
    "ContrastParams",
    "OpticalContext",
    "OpticalSpacingResult",
    "apply",
    "apply_overshoot",
    "cleanup_joins",
    "equalize_vertical_stems",
    "fit_kern_pair",
    "measure_side_whitespace",
    "measure_vertical_stem",
    "pair_gap_bbox",
    "pair_gap_optical",
    "space_word_optical",
    "suggest_sidebearings",
    "suggest_sidebearings_optical",
    "validate_contrast_params",
    "with_sidebearings",
]
