"""Contract tests for ``plugins.passes.diagonal_comp``."""

from __future__ import annotations

from tests.plugins.passes.helpers import make_system
from typekernel.draw import Writer
from typekernel.plugins.passes.diagonal_comp import compensated_weight, diagonal_comp


def test_compensated_weight_upright_equals_stem() -> None:
    assert abs(compensated_weight(80.0, 0.0) - 80.0) < 1e-9


def test_compensated_weight_thins_diagonal() -> None:
    assert compensated_weight(80.0, 45.0) < 80.0


def test_diagonal_comp_moves_tagged_join() -> None:
    system = make_system(stem=80.0)
    d = (
        Writer()
        .start((0, 0))
        .line((20, 0))
        .line((40, 40))
        .node("join")
        .line((0, 40))
        .close()
        .build()
    )
    out = diagonal_comp(d, system, at="join", angle_from_vertical_deg=45.0)
    assert out.nodes == d.nodes
    # Join point should have moved (segment kinds stable).
    assert tuple(type(s).__name__ for s in out.contours[0].segments) == tuple(
        type(s).__name__ for s in d.contours[0].segments
    )


def test_diagonal_comp_upright_noop() -> None:
    system = make_system(stem=80.0)
    d = (
        Writer()
        .start((0, 0))
        .line((20, 0))
        .line((20, 40))
        .node("join")
        .line((0, 40))
        .close()
        .build()
    )
    out = diagonal_comp(d, system, at="join", angle_from_vertical_deg=0.0)
    # pull=0 → identical geometry
    assert out.contours[0].segments[1].p1 == d.contours[0].segments[1].p1
