"""Tests for explicit join cleanup."""

from pathlib import Path

import pytest

from typekernel.geo.fixtures import load_synthetic_outline
from typekernel.optics.joins import cleanup_joins

FIXTURE = Path(__file__).parent.parent / "fixtures" / "synthetic_O.json"


def test_noop_is_identity() -> None:
    outline = load_synthetic_outline(FIXTURE)
    assert cleanup_joins(outline, policy="noop") is outline


def test_reserved_policies_raise() -> None:
    outline = load_synthetic_outline(FIXTURE)
    with pytest.raises(NotImplementedError):
        cleanup_joins(outline, policy="tangent_fix")
    with pytest.raises(NotImplementedError):
        cleanup_joins(outline, policy="ink_trap")
