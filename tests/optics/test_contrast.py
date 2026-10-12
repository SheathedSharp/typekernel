"""Tests for contrast parameter validation."""

import pytest

from typekernel.optics.contrast import ContrastParams, validate_contrast_params


def test_valid_contrast() -> None:
    validate_contrast_params(ContrastParams(thick=100.0, thin=40.0))


def test_thick_equals_thin_ok() -> None:
    validate_contrast_params(ContrastParams(thick=50.0, thin=50.0))


def test_thin_non_positive_raises() -> None:
    with pytest.raises(ValueError, match="thick >= thin > 0"):
        validate_contrast_params(ContrastParams(thick=10.0, thin=0.0))


def test_thick_less_than_thin_raises() -> None:
    with pytest.raises(ValueError, match="thick >= thin > 0"):
        validate_contrast_params(ContrastParams(thick=10.0, thin=20.0))


def test_docstring_forbids_stroke_expand() -> None:
    doc = (ContrastParams.__doc__ or "").lower()
    assert "stroke expand" in doc or "not stroke" in doc or "buffer" in doc
