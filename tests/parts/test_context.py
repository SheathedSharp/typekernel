"""Tests for DesignContext rhythm parameters."""

from typekernel.parts import DesignContext


def test_geometric_sans_factory() -> None:
    ctx = DesignContext.geometric_sans()
    assert ctx.units_per_em == 1000.0
    assert ctx.stem > 0
    assert 0.5 <= ctx.contrast <= 1.2
    assert ctx.thin == ctx.stem * ctx.contrast


def test_join_radius_from_roundness() -> None:
    ctx = DesignContext(stem=100.0, roundness=0.4)
    assert ctx.join_radius == 40.0
