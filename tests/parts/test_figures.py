"""Lining figures from the cap H / O records, and tabular spacing."""

from __future__ import annotations

import pytest

from typekernel.geo.contour import signed_area
from typekernel.geo.layout import union_bounds
from typekernel.geo.outline import bounds
from typekernel.optics.space import ink_intervals_at_y
from typekernel.parts import FIGURE_FORMS, Controls, DesignContext, h_cap_metrics, tabular
from typekernel.parts.figures import FIGURE_STEM_RATIO

COUNTERS = {"0": 1, "4": 1, "6": 1, "8": 2, "9": 1}


@pytest.fixture
def ctx() -> DesignContext:
    return DesignContext.code_clear()


@pytest.fixture
def figures(ctx: DesignContext):
    return Controls.from_context(ctx).build_all("0123456789")


def test_all_ten_registered() -> None:
    assert "".join(sorted(FIGURE_FORMS)) == "0123456789"


@pytest.mark.parametrize("ch", list("0123456789"))
def test_outer_plus_counters(figures, ch: str) -> None:
    outer, *rest = (k for s in figures[ch].solids for k in s.contours)
    assert signed_area(outer) > 0
    assert len(rest) == COUNTERS.get(ch, 0)
    assert all(signed_area(k) < 0 for k in rest)


def test_lining_height(figures, ctx: DesignContext) -> None:
    for ch, g in figures.items():
        _, y0, _, y1 = union_bounds(list(g.solids))
        assert y1 == pytest.approx(ctx.cap_height, abs=ctx.overshoot + 0.5), ch
        assert y0 == pytest.approx(0.0, abs=ctx.overshoot + 0.5), ch


def test_figure_stroke_lighter_than_cap_stem(figures, ctx: DesignContext) -> None:
    t = h_cap_metrics(ctx).stem * FIGURE_STEM_RATIO
    (stem,) = ink_intervals_at_y(list(figures["1"].solids), ctx.cap_height * 0.3)
    assert stem[1] - stem[0] == pytest.approx(t)
    assert t < h_cap_metrics(ctx).stem


def test_tabular_gives_one_advance_with_centred_ink(figures) -> None:
    tab = tabular(figures)
    advances = {g.advance for g in tab.values()}
    assert len(advances) == 1
    adv = advances.pop()
    assert adv == pytest.approx(max(g.advance for g in figures.values()))
    for ch, g in tab.items():
        x0, _, x1, _ = union_bounds(list(g.solids))
        assert x0 == pytest.approx(adv - x1, abs=1e-6), ch
        assert g.anchors == tuple(
            type(a)(a.name, a.x + (x0 - bounds(figures[ch].solids[0])[0]), a.y)
            for a in figures[ch].anchors
        )


def test_tabular_explicit_advance(figures) -> None:
    tab = tabular(figures, advance=700.0)
    assert {g.advance for g in tab.values()} == {700.0}
    assert tabular({}) == {}
