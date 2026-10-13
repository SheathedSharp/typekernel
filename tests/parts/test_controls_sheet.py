"""Controls: one sheet, one adjustment, the whole lowercase family follows."""

from __future__ import annotations

import pytest

from typekernel.geo.outline import bounds
from typekernel.parts import RELATED_FORMS, Controls, DesignContext, n_metrics, o_metrics


@pytest.fixture
def ctx() -> DesignContext:
    return DesignContext.code_clear()


def _width(g) -> float:
    b = bounds(g.solids[0])
    return b[2] - b[0]


def test_build_all_covers_related_forms(ctx: DesignContext) -> None:
    glyphs = Controls.from_context(ctx).build_all()
    assert set(glyphs) == set(RELATED_FORMS) == set("bdhilmnopqru")
    assert all(g.advance > 0 for g in glyphs.values())


def test_tuned_n_moves_n_family_only(ctx: DesignContext) -> None:
    base = Controls.from_context(ctx).build_all()
    wide = Controls.from_context(ctx).tuned_n(counter=n_metrics(ctx).counter + 60).build_all()
    for ch in "nhu":
        assert _width(wide[ch]) == pytest.approx(_width(base[ch]) + 60)
    assert _width(wide["m"]) > _width(base["m"])
    assert _width(wide["r"]) > _width(base["r"])
    for ch in "obdpq":
        assert _width(wide[ch]) == pytest.approx(_width(base[ch]))


def test_tuned_o_moves_o_family_only(ctx: DesignContext) -> None:
    base = Controls.from_context(ctx).build_all()
    wide = Controls.from_context(ctx).tuned_o(rx=o_metrics(ctx).rx + 25).build_all()
    for ch in "obdpq":
        assert _width(wide[ch]) == pytest.approx(_width(base[ch]) + 50)
    for ch in "nhmrui":
        assert _width(wide[ch]) == pytest.approx(_width(base[ch]))


def test_stem_change_reaches_bowl_letters(ctx: DesignContext) -> None:
    from typekernel.optics.space import ink_intervals_at_y

    glyphs = Controls.from_context(ctx).tuned_n(stem=120.0).build("d")
    (interval,) = ink_intervals_at_y(list(glyphs.solids), ctx.ascender - 20)
    assert interval[1] - interval[0] == pytest.approx(120.0, abs=0.01)


def test_build_subset_and_unknown(ctx: DesignContext) -> None:
    controls = Controls.from_context(ctx)
    assert list(controls.build_all("hoh")) == ["h", "o"]
    with pytest.raises(KeyError, match="no related form"):
        controls.build_all("nz")
