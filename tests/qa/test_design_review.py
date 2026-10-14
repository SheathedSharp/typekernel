"""design_review tells an agent the next edit; it does not approve a family."""

from __future__ import annotations

from pathlib import Path

import pytest

from typekernel.parts import Controls, DesignContext
from typekernel.parts.control import f_from_n, t_from_n
from typekernel.qa.design_review import WEAK_GLYPHS, design_review


def _l0_trial() -> Controls:
    ctx = DesignContext.humanist_sans().tuned(sidebearing_ratio=0.11)
    controls = Controls.from_context(ctx)
    controls = controls.with_glyph("f", lambda n, o, c: f_from_n(n, c, arm=0.82))
    controls = controls.with_glyph("t", lambda n, o, c: t_from_n(n, c, arm=0.58))
    return controls


def test_l0_trial_beats_or_matches_preset() -> None:
    review = design_review(
        _l0_trial(),
        baseline=Controls.from_context(DesignContext.humanist_sans()),
    )
    assert review.failures == (), review.failures
    assert review.l0_gaps == ()
    ratio = next(delta for delta in review.deltas if delta.name == "optical_gap_ratio")
    assert ratio.worse is False
    assert ratio.trial <= ratio.baseline + 1e-3
    assert review.worst_pairs
    assert review.worst_pairs[0].min_gap > 0.0
    overridden = {glyph.char for glyph in review.glyphs if glyph.overridden}
    assert len(overridden & set(WEAK_GLYPHS)) >= 2
    assert "no preset baseline" not in " ".join(review.notes)


def test_missing_weak_overrides_is_an_l0_gap() -> None:
    review = design_review(Controls.from_context(DesignContext.code_clear()))
    assert review.l0_gaps
    assert any("with_glyph" in gap for gap in review.l0_gaps)
    assert any("no preset baseline" in note for note in review.notes)


def test_review_writes_json_and_control_pngs(tmp_path: Path) -> None:
    pytest.importorskip("PIL")
    review = design_review(
        _l0_trial(),
        baseline=Controls.from_context(DesignContext.humanist_sans()),
        out_dir=tmp_path,
    )
    assert (tmp_path / "review.json").is_file()
    assert (tmp_path / "contact.png").is_file()
    assert (tmp_path / "index.json").is_file()
    assert (tmp_path / "n.png").is_file()
    assert (tmp_path / "f.png").is_file()
    assert "sentence gate ok" in review.summary()
