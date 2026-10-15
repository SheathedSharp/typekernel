"""Agent trial protocol (TK-502)."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

from typekernel.parts import Controls, DesignContext
from typekernel.qa.originality import L3_MIN_TOPOLOGY_FRACTION
from typekernel.qa.trial_protocol import (
    FIXED_TRIAL_BRIEFS,
    HUMAN_REVIEW_SCORE_KEYS,
    L3_VOICE_DISTANCE_THRESHOLD,
    WEIGHT_LADDER_STEMS,
    controls_at_ladder_stem,
    snapshot_trial,
    trial_snapshot_exit_code,
    human_review_scores_complete,
    trial_snapshot_json_exit_code,
    validate_trial_snapshot,
    validate_trial_snapshot_json,
    validate_trial_snapshot_record,
    voice_distance,
    weight_ladder_r8_failures,
    write_trial_snapshot,
)

_ROOT = Path(__file__).resolve().parents[2]
_SLAB_TRIAL = _ROOT / "examples" / "agent_trial" / "design_editorial_slab.py"

_PRESET_FACTORIES = {
    "humanist_sans": DesignContext.humanist_sans,
    "geometric_sans": DesignContext.geometric_sans,
    "code_clear": DesignContext.code_clear,
}


def test_weight_ladder_stems_include_black_master() -> None:
    assert WEIGHT_LADDER_STEMS[-1] == 200.0


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
    assert not snap.cheating_flags
    assert snap.voice_distance < 1e-5
    assert not snap.l3_voice_ok


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
    assert snap.weight_ladder_r8_failures == 0
    assert snap.voice_distance >= L3_VOICE_DISTANCE_THRESHOLD
    assert snap.l3_voice_ok


def test_trial_snapshot_json_exit_code_8_when_human_scores_required_but_missing() -> None:
    payload = {
        "cheating_flags": [],
        "family_gate_ok": True,
        "identity_error_count": 0,
        "l3_voice_ok": True,
        "lint_error_count": 0,
        "program_pass_ok": True,
        "topology_fraction": 0.2,
        "voice_distance": L3_VOICE_DISTANCE_THRESHOLD + 0.1,
        "weight_ladder_r8_failures": 0,
    }
    assert trial_snapshot_json_exit_code(payload, ()) == 0
    assert trial_snapshot_json_exit_code(payload, (), require_human_scores=True) == 8
    payload["human_review_scores"] = {key: 4 for key in HUMAN_REVIEW_SCORE_KEYS}
    assert human_review_scores_complete(payload)
    assert trial_snapshot_json_exit_code(payload, (), require_human_scores=True) == 0


def test_validate_trial_snapshot_record_accepts_human_review_scores() -> None:
    scores = {key: 4 for key in HUMAN_REVIEW_SCORE_KEYS}
    problems = validate_trial_snapshot_record(
        {
            "cheating_flags": [],
            "family_gate_ok": True,
            "human_review_scores": scores,
            "identity_error_count": 0,
            "l3_voice_ok": True,
            "lint_error_count": 0,
            "program_pass_ok": True,
            "topology_fraction": 0.2,
            "voice_distance": L3_VOICE_DISTANCE_THRESHOLD + 0.1,
            "weight_ladder_r8_failures": 0,
        }
    )
    assert not problems


def test_validate_trial_snapshot_record_rejects_invalid_human_review_scores() -> None:
    problems = validate_trial_snapshot_record(
        {
            "human_review_scores": {"readable": 6},
        }
    )
    assert problems
    assert any("readable" in p for p in problems)


def test_validate_trial_snapshot_record_rejects_forged_program_pass_ok() -> None:
    problems = validate_trial_snapshot_record(
        {
            "cheating_flags": [],
            "family_gate_ok": True,
            "identity_error_count": 0,
            "l3_voice_ok": False,
            "lint_error_count": 0,
            "program_pass_ok": True,
            "topology_fraction": 0.2,
            "voice_distance": L3_VOICE_DISTANCE_THRESHOLD + 0.1,
            "weight_ladder_r8_failures": 0,
        }
    )
    assert problems
    assert any("program_pass_ok" in p for p in problems)


def test_validate_trial_snapshot_record_rejects_forged_l3_with_zero_topology() -> None:
    """TK-307: high voice_distance alone must not imply l3_voice_ok in JSON."""
    problems = validate_trial_snapshot_record(
        {
            "cheating_flags": (),
            "voice_distance": L3_VOICE_DISTANCE_THRESHOLD + 0.1,
            "topology_fraction": 0.0,
            "l3_voice_ok": True,
        }
    )
    assert problems
    assert any("topology_fraction" in p for p in problems)


def test_stem_only_tweak_records_cheating_flag_and_exit_code_7() -> None:
    ctx = DesignContext.humanist_sans()
    tweaked = Controls.from_context(ctx.tuned(stem=ctx.stem * 1.05))
    snap = snapshot_trial(tweaked, brief=FIXED_TRIAL_BRIEFS[0])
    assert not snap.l3_voice_ok
    assert snap.topology_fraction < L3_MIN_TOPOLOGY_FRACTION
    assert snap.cheating_flags == ("stem_only_or_scale_voice",)
    assert not validate_trial_snapshot(snap)
    assert not snap.program_pass_ok
    assert trial_snapshot_exit_code(snap, validate_trial_snapshot(snap)) == 7


def test_trial_snapshot_json_exit_code_matches_live_snapshot(tmp_path: Path) -> None:
    spec = importlib.util.spec_from_file_location(
        "warm",
        _ROOT / "examples" / "agent_trial" / "design_warm_humanist.py",
    )
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    snap = snapshot_trial(mod.controls(), brief=FIXED_TRIAL_BRIEFS[0])
    path = write_trial_snapshot(tmp_path / "snapshot.json", snap)
    problems = validate_trial_snapshot_json(path)
    assert not problems
    data = json.loads(path.read_text(encoding="utf-8"))
    assert trial_snapshot_json_exit_code(data, problems) == 0
    assert trial_snapshot_exit_code(snap, validate_trial_snapshot(snap)) == 0


def test_written_snapshot_json_passes_validate_record(tmp_path: Path) -> None:
    spec = importlib.util.spec_from_file_location(
        "warm",
        _ROOT / "examples" / "agent_trial" / "design_warm_humanist.py",
    )
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    snap = snapshot_trial(mod.controls(), brief=FIXED_TRIAL_BRIEFS[0])
    path = write_trial_snapshot(tmp_path / "snapshot.json", snap)
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["program_pass_ok"] is True
    assert data["cheating_flags"] == []
    assert not validate_trial_snapshot_record(data)


def test_validate_trial_snapshot_clean_on_reference_warm_humanist() -> None:
    spec = importlib.util.spec_from_file_location(
        "warm",
        _ROOT / "examples" / "agent_trial" / "design_warm_humanist.py",
    )
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    snap = snapshot_trial(mod.controls(), brief=FIXED_TRIAL_BRIEFS[0])
    assert not validate_trial_snapshot(snap)


def test_snapshot_l3_voice_ok_rejects_stem_only_tweak() -> None:
    """TK-502 / TK-307: trial JSON must not treat pure stem scaling as L3."""
    ctx = DesignContext.humanist_sans()
    tweaked = Controls.from_context(ctx.tuned(stem=ctx.stem * 1.05))
    snap = snapshot_trial(tweaked, brief=FIXED_TRIAL_BRIEFS[0], apis_used=("stem_tweak",))
    assert snap.voice_distance >= L3_VOICE_DISTANCE_THRESHOLD
    assert not snap.l3_voice_ok
    assert snap.topology_fraction == 0.0
    assert snap.cheating_flags == ("stem_only_or_scale_voice",)


def test_voice_distance_zero_on_unchanged_preset() -> None:
    controls = Controls.from_context(DesignContext.humanist_sans())
    assert voice_distance(controls) < 1e-6


def test_voice_distance_increases_with_tuned_glyph() -> None:
    base = Controls.from_context(DesignContext.humanist_sans())
    tuned = base.tuned_glyph("f", arm=0.55).tuned_glyph("t", arm=0.45)
    assert voice_distance(tuned) > voice_distance(base)
    assert voice_distance(tuned) > 0.0


def test_weight_ladder_r8_uses_glyph_overrides_not_context_only() -> None:
    """Ladder R8 must match the trial sheet (``with_glyph`` / ``tuned_glyph``)."""
    spec = importlib.util.spec_from_file_location("slab_trial", _SLAB_TRIAL)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    sheet: Controls = mod.controls()
    assert weight_ladder_r8_failures(sheet) == 0
    bare = Controls.from_context(sheet.context)
    assert weight_ladder_r8_failures(bare) == 0
    at_70 = controls_at_ladder_stem(sheet, 70.0)
    assert "f" in at_70.glyph_overrides


def test_snapshot_records_glyph_specs(tmp_path) -> None:
    brief = FIXED_TRIAL_BRIEFS[0]
    controls = Controls.from_context(DesignContext.humanist_sans()).tuned_glyph("f", arm=0.8)
    snap = snapshot_trial(controls, brief=brief, apis_used=("manual",))
    assert "f" in snap.glyph_spec_chars
    assert "tuned_glyph" in snap.apis_used
    path = write_trial_snapshot(tmp_path / "snap.json", snap)
    assert path.is_file()
    assert "voice_distance" in path.read_text(encoding="utf-8")
