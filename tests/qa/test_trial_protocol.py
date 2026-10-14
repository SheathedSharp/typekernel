"""Agent trial protocol (TK-502)."""

from __future__ import annotations

from typekernel.parts import Controls, DesignContext
from typekernel.qa.trial_protocol import (
    FIXED_TRIAL_BRIEFS,
    snapshot_trial,
    voice_distance,
    write_trial_snapshot,
)


def test_fixed_briefs_are_three_and_unique() -> None:
    assert len(FIXED_TRIAL_BRIEFS) == 3
    assert len({b.id for b in FIXED_TRIAL_BRIEFS}) == 3


def test_voice_distance_zero_on_unchanged_preset() -> None:
    controls = Controls.from_context(DesignContext.humanist_sans())
    assert voice_distance(controls) < 1e-6


def test_voice_distance_increases_with_tuned_glyph() -> None:
    base = Controls.from_context(DesignContext.humanist_sans())
    tuned = base.tuned_glyph("f", arm=0.55).tuned_glyph("t", arm=0.45)
    assert voice_distance(tuned) > voice_distance(base)
    assert voice_distance(tuned) > 0.0


def test_snapshot_records_glyph_specs(tmp_path) -> None:
    brief = FIXED_TRIAL_BRIEFS[0]
    controls = Controls.from_context(DesignContext.humanist_sans()).tuned_glyph("f", arm=0.8)
    snap = snapshot_trial(controls, brief=brief, apis_used=("manual",))
    assert "f" in snap.glyph_spec_chars
    assert "tuned_glyph" in snap.apis_used
    path = write_trial_snapshot(tmp_path / "snap.json", snap)
    assert path.is_file()
    assert "voice_distance" in path.read_text(encoding="utf-8")
