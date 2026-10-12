"""Tests for the reserved sidebearing stub."""

import pytest

from typekernel.geo.outline import Outline
from typekernel.optics.context import OpticalContext
from typekernel.optics.sidebearing import suggest_sidebearings


def test_suggest_sidebearings_raises() -> None:
    with pytest.raises(NotImplementedError, match="reserved"):
        suggest_sidebearings(Outline(()), OpticalContext())
