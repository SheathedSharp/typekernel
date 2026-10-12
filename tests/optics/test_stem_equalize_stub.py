"""Tests for the reserved stem-equalization stub."""

import pytest

from typekernel.geo.outline import Outline
from typekernel.optics.context import OpticalContext
from typekernel.optics.stem import equalize_vertical_stems


def test_equalize_vertical_stems_raises() -> None:
    with pytest.raises(NotImplementedError, match="reserved"):
        equalize_vertical_stems(Outline(()), target_width=80.0, ctx=OpticalContext())
