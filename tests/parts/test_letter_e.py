"""letter_e keeps its crossbar and opens an aperture; ring ∪ bar is a real union."""

from __future__ import annotations

import pytest

pytest.importorskip("pathops")

from typekernel.geo.contour import signed_area
from typekernel.geo.outline import bounds
from typekernel.optics.space import ink_intervals_at_y
from typekernel.parts import DesignContext, bowl, crossbar
from typekernel.parts.compose import try_difference, try_union
from typekernel.parts.latin import letter_e


@pytest.mark.parametrize("preset", ["geometric_sans", "paper_ink", "code_clear"])
def test_e_has_crossbar_and_aperture(preset: str) -> None:
    ctx = getattr(DesignContext, preset)()
    g = letter_e(ctx)
    x0, _, x1, _ = bounds(g.solids[0])
    bar_y = ctx.x_height / 2.0 + ctx.stem * 0.05

    # Through the bar: one ink run across the whole letter.
    (run,) = ink_intervals_at_y(list(g.solids), bar_y)
    assert run[0] == pytest.approx(x0, abs=1.0)
    assert run[1] == pytest.approx(x1, abs=1.0)

    # Just under the bar: the right wall is open (aperture).
    below = ink_intervals_at_y(list(g.solids), bar_y - ctx.thin / 2.0 - 5.0)
    assert max(b for _, b in below) < x1 - ctx.stem


def test_union_with_a_counter_is_not_xor() -> None:
    ctx = DesignContext.code_clear()
    outer, hole = bowl(ctx, 300, 260, rx=280, ry=270, thickness=ctx.stem)
    ring = try_difference(outer, hole)
    bar = crossbar(ctx, 300 - 280 + ctx.stem / 2, 300 + 280 - ctx.stem / 2, 260, thickness=60)
    merged = try_union([ring, bar])
    areas = sorted(signed_area(c) for c in merged.contours)
    # One outer and the two counters above and below the bar — no overlap holes.
    assert len(areas) == 3
    assert areas[-1] > 0 > areas[0]
