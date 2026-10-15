"""TK-502: committed trial protocol doc stays complete."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_agent_trials_documents_final_validation_and_human_review() -> None:
    text = (ROOT / "docs" / "AGENT_TRIALS.md").read_text(encoding="utf-8")
    assert "终验" in text
    assert "human_review_bundle" in text
    assert "brief-1" in text
    assert "tk502_reference_metrics" in text or "reference_metrics" in text
