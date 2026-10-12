"""Unit tests for the ConversionReport type."""

from dataclasses import FrozenInstanceError

import pytest

from typekernel.geo.convert_quadratic import ConversionReport


def _report() -> ConversionReport:
    return ConversionReport(
        max_error=0.25,
        segment_count_in=4,
        segment_count_out=9,
        budget=1.0,
    )


def test_construction_keeps_every_field() -> None:
    report = _report()
    assert report.max_error == 0.25
    assert report.segment_count_in == 4
    assert report.segment_count_out == 9
    assert report.budget == 1.0


def test_equality_is_by_value() -> None:
    assert _report() == _report()


def test_report_is_frozen() -> None:
    with pytest.raises(FrozenInstanceError):
        _report().max_error = 99.0


def test_report_is_hashable() -> None:
    assert len({_report(), _report()}) == 1
