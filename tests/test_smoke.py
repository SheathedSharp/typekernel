"""Smoke tests: the package imports and still reports its scaffold version."""

import typekernel


def test_package_imports() -> None:
    """typekernel resolves as an installed package, not a stray directory."""
    assert typekernel.__name__ == "typekernel"


def test_scaffold_version() -> None:
    """Version stays at 0.0.0 until a release task deliberately bumps it."""
    assert typekernel.__version__ == "0.0.0"
