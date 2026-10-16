"""TK-502: committed trial protocol doc stays complete."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_agent_trials_documents_final_validation_and_human_review() -> None:
    text = (ROOT / "docs" / "AGENT_TRIALS.md").read_text(encoding="utf-8")
    assert "终验" in text
    assert "program_pass_ok" in text
    assert "cheating_flags" in text
    assert "topology_fraction" in text
    assert "human_review_scores" in text
    assert "human_review_bundle" in text
    assert "brief-1" in text
    assert "reference_trial_metrics" in text or "reference_metrics" in text
    assert "test_development_plan_section8" in text
    assert "run_program_exit" in text
    assert "validate_snapshot.py" in text
    assert "test_agent_trial.py" in text or "test_agent_trial" in text
    assert "contact_sheet.py" in text
    assert "weight_ladder_sheet.py" in text
    assert "regenerate_outline_hashes.py" in text
    assert "--only appendix-b" in text
    assert "B-13" in text or "B-13–B-15" in text
    assert "appendix_b_three_g_humanist.png" in text
    assert "test_known_defects" in text
    assert "test_gate_thresholds_locked" in text
    assert "test_b13_" in text
    assert "test_extended_latin_policy" in text
    assert "test_multi_voice_exit" in text
    assert "test_zayju_script_sequential_style_gate_passes" in text
    assert "test_knob_coverage" in text
    assert "test_style_consistency" in text
    assert "test_originality" in text
