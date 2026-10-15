"""Agent trial protocol (TK-502)."""

from __future__ import annotations

import pytest

from typekernel.parts import Controls, DesignContext
from typekernel.qa.trial_protocol import (
    FIXED_TRIAL_BRIEFS,
    L3_VOICE_DISTANCE_THRESHOLD,
    snapshot_trial,
    voice_distance,
    write_trial_snapshot,
)

_PRESET_FACTORIES = {
    "humanist_sans": DesignContext.humanist_sans,
    "geometric_sans": DesignContext.geometric_sans,
    "code_clear": DesignContext.code_clear,
}


def test_fixed_briefs_are_three_and_unique() -> None:
    assert len(FIXED_TRIAL_BRIEFS) == 3
    assert len({b.id for b in FIXED_TRIAL_BRIEFS}) == 3


@pytest.mark.parametrize("brief", FIXED_TRIAL_BRIEFS)
def test_preset_brief_snapshots_pass_gate(brief) -> None:
    """Unmodified presets must pass §6 gate metrics (M5 baseline)."""
    factory = _PRESET_FACTORIES[brief.preset]
    controls = Controls.from_context(factory())
    snap = snapshot_trial(controls, brief=brief, round=0, apis_used=("preset_only",))
    assert snap.family_gate_ok, snap.family_gate_failures
    assert snap.metrics_ok
    assert snap.lint_error_count == 0
    assert snap.identity_error_count == 0
    assert snap.weight_ladder_r8_failures == 0


@pytest.mark.parametrize(
    "factory",
    (DesignContext.slab_serif, DesignContext.bracketed_serif),
)
def test_serif_voice_trial_snapshots_meet_l3(factory) -> None:
    """TK-306 voices are valid L3 trial starting points (TK-502 baseline)."""
    controls = Controls.from_context(factory())
    snap = snapshot_trial(
        controls,
        brief=FIXED_TRIAL_BRIEFS[1],
        round=0,
        apis_used=("preset_only", "serif_voice"),
    )
    assert snap.family_gate_ok, snap.family_gate_failures
    assert snap.metrics_ok
    assert snap.voice_distance >= L3_VOICE_DISTANCE_THRESHOLD


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
