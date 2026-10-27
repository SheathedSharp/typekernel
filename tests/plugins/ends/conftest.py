"""Fixtures for end-plugin tests."""

from __future__ import annotations

import pytest

from tests.plugins.ends.helpers import make_system
from typekernel.system import System


@pytest.fixture
def system() -> System:
    return make_system()
