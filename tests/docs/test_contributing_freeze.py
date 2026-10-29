"""CONTRIBUTING documents the pre-P2 freeze."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_contributing_has_current_phase_freeze() -> None:
    text = (ROOT / "CONTRIBUTING.md").read_text(encoding="utf-8")
    assert "当前阶段" in text
    assert "P2" in text
    assert "starter" in text.lower()
    assert "see" in text.lower() or "explain" in text.lower()
