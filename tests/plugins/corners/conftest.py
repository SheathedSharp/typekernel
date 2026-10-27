"""Pytest fixtures for corner-plugin contract tests."""

from __future__ import annotations

import pytest

from tests.plugins.corners.helpers import make_system
from typekernel.system import System


@pytest.fixture
def system() -> System:
    return make_system()
