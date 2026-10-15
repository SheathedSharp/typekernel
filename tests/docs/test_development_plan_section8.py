"""DEVELOPMENT_PLAN §8: programmatic exit criteria (excludes human trial sign-off)."""

from __future__ import annotations

import re
from pathlib import Path

import pytest

_XFAIL_DECORATOR = re.compile(r"@pytest\.mark\.xfail\b")

from typekernel.qa.gates import ApprovalError, load_approval, require_approval

ROOT = Path(__file__).resolve().parents[2]

_SECTION8_DOC_PATHS = (
    "docs/AGENT_GOAL.md",
    ".agents/skills/typekernel-font-design/SKILL.md",
    "docs/agent-recipes.md",
    "docs/VISION.md",
    "README.md",
)

_PENDING_HUMAN_GATES = (
    "approvals/serif-slab-voice.json",
    "approvals/serif-bracketed-voice.json",
    "approvals/italic-vf-construct.json",
)


def test_section8_tk106_has_no_strict_xfail_markers() -> None:
    """§8.2: defect registry tests must not use strict xfail."""
    tests_root = ROOT / "tests"
    for path in tests_root.rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        assert not _XFAIL_DECORATOR.search(text), (
            f"remove xfail from {path.relative_to(ROOT)}"
        )


def test_section8_required_docs_exist() -> None:
    """§8.7: core agent-facing docs remain in the tree."""
    for rel in _SECTION8_DOC_PATHS:
        assert (ROOT / rel).is_file(), rel


def test_section8_human_gates_remain_pending_until_review() -> None:
    """§8.6 / TK-306 / TK-402: agents must not ship with auto-approved visual gates."""
    for rel in _PENDING_HUMAN_GATES:
        data = load_approval(ROOT / rel)
        assert data["approved"] is False
        assert data["approver"] == ""
        with pytest.raises(ApprovalError, match="not approved"):
            require_approval(ROOT / rel)


def test_section8_agent_trials_documents_final_validation() -> None:
    """§8.6: final agent trial is documented separately from reference builds."""
    text = (ROOT / "docs" / "AGENT_TRIALS.md").read_text(encoding="utf-8")
    assert "终验" in text
    assert "作废条件" in text
    assert "human_review_bundle" in text
