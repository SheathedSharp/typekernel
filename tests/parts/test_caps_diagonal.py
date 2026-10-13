"""A V W X Y Z K M N: compensated diagonals on the cap H record."""

from __future__ import annotations

import pytest

from typekernel.geo.contour import signed_area
from typekernel.geo.outline import bounds
from typekernel.optics.space import ink_intervals_at_y
from typekernel.parts import CAP_FORMS, Controls, DesignContext, h_cap_metrics


@pytest.fixture
def ctx() -> DesignContext:
    return DesignContext.code_clear()


@pytest.fixture
def caps(ctx: DesignContext):
    return Controls.from_context(ctx).build_all("AVWXYZKMN")


def test_full_cap_alphabet_registered() -> None:
    assert "".join(sorted(CAP_FORMS)) == "ABCDEFGHIJKLMNOPQRSTUVWXYZ"


@pytest.mark.parametrize("ch", list("VWXYZKMN"))
def test_single_polygon_on_zones(caps, ctx: DesignContext, ch: str) -> None:
    (contour,) = caps[ch].solids[0].contours
    assert signed_area(contour) > 0
    assert all(s.kind == "line" for s in contour.segments)
    _, y0, _, y1 = bounds(caps[ch].solids[0])
    assert (y0, y1) == pytest.approx((0.0, ctx.cap_height))


def test_a_has_bar_and_counter(caps, ctx: DesignContext) -> None:
    outer, counter = caps["A"].solids[0].contours
    assert signed_area(outer) > 0 > signed_area(counter)
    bar_y = 0.28 * ctx.cap_height
    assert len(ink_intervals_at_y(list(caps["A"].solids), bar_y)) == 1  # crossbar
    assert len(ink_intervals_at_y(list(caps["A"].solids), 5.0)) == 2  # two legs


def test_heavy_a_widens_to_keep_its_counter() -> None:
    heavy = DesignContext.code_clear().tuned(stem=220.0)
    a = Controls.from_context(heavy).build("A")
    assert len(a.solids[0].contours) == 2
    x0, _, x1, _ = bounds(a.solids[0])
    assert x1 - x0 >= 3.2 * h_cap_metrics(heavy).stem - 1e-6


def test_m_and_n_stems_are_cap_stems(caps, ctx: DesignContext) -> None:
    t = h_cap_metrics(ctx).stem
    # stems stand alone where no diagonal joins them
    for ch, y, side in (("M", 5.0, 0), ("M", 5.0, -1), ("N", 5.0, 0), ("N", ctx.cap_height - 5, -1)):
        runs = ink_intervals_at_y(list(caps[ch].solids), y)
        assert runs[side][1] - runs[side][0] == pytest.approx(t), (ch, y)


def test_m_vertex_on_baseline_and_y_stem_vertical(caps, ctx: DesignContext) -> None:
    m_runs = ink_intervals_at_y(list(caps["M"].solids), 2.0)
    assert len(m_runs) == 3  # two stems and the vertex
    t = h_cap_metrics(ctx).stem
    for y in (5.0, ctx.cap_height * 0.3):
        (stem,) = ink_intervals_at_y(list(caps["Y"].solids), y)
        assert stem[1] - stem[0] == pytest.approx(t)


def test_k_arm_reaches_cap_height(caps, ctx: DesignContext) -> None:
    assert len(ink_intervals_at_y(list(caps["K"].solids), ctx.cap_height - 2.0)) == 2
