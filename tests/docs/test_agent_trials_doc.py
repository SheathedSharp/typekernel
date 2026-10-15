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
    assert "tk502_reference_metrics" in text or "reference_metrics" in text
    assert "test_development_plan_section8" in text
    assert "run_m5_program_exit" in text
    assert "validate_snapshot.py" in text
    assert "test_agent_trial.py" in text or "test_agent_trial" in text
