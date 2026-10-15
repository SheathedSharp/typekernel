"""DEVELOPMENT_PLAN §8: programmatic exit criteria (excludes human trial sign-off)."""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from typekernel.qa.gates import ApprovalError, load_approval, require_approval

_XFAIL_DECORATOR = re.compile(r"@pytest\.mark\.xfail\b")

ROOT = Path(__file__).resolve().parents[2]

_SECTION8_DOC_PATHS = (
    "docs/AGENT_GOAL.md",
    ".agents/skills/typekernel-font-design/SKILL.md",
    "docs/agent-recipes.md",
    "docs/dev-standards.md",
    "docs/VISION.md",
    "README.md",
)

_PENDING_HUMAN_GATES = (
    "approvals/serif-slab-voice.json",
    "approvals/serif-bracketed-voice.json",
    "approvals/italic-vf-construct.json",
)

_SECTION8_REGRESSION_TESTS: tuple[tuple[str, tuple[str, ...]], ...] = (
    (
        "tests/parts/test_knob_coverage.py",
        (
            "test_contrast_moves_round_letters",
            "test_terminal_style_reaches_many_glyphs",
        ),
    ),
    (
        "tests/parts/test_italic_controls.py",
        ("test_italic_construct_slant_matches_target_within_half_degree",),
    ),
    (
        "tests/parts/test_italic_topology.py",
        ("test_italic_design_differs_from_construct_oblique_on_key_letters",),
    ),
    (
        "tests/parts/test_serifs.py",
        ("test_serif_voice_meets_tk306_program_acceptance",),
    ),
    (
        "tests/parts/test_italic_program_acceptance.py",
        ("test_italic_vf_meets_tk402_program_acceptance_on_humanist",),
    ),
    (
        "tests/qa/test_m3_exit.py",
        (
            "test_m3_three_l3_voices_slab_bracketed_and_reference_sans",
            "test_m3_serif_pair_differs_from_warm_humanist_reference",
        ),
    ),
    (
        "tests/qa/test_originality.py",
        (
            "test_l3_rejects_context_only_stem_tweak",
            "test_tk307_serif_voices_far_from_every_builtin_preset",
        ),
    ),
    (
        "tests/parts/test_tk208_extended_latin.py",
        ("test_extended_latin_not_in_default_supported",),
    ),
    (
        "tests/parts/test_tk308_program_acceptance.py",
        ("test_tk308_stroke_spike_meets_program_acceptance",),
    ),
    (
        "tests/qa/test_trial_protocol.py",
        (
            "test_snapshot_l3_voice_ok_rejects_stem_only_tweak",
            "test_validate_trial_snapshot_record_rejects_forged_l3_with_zero_topology",
            "test_validate_trial_snapshot_record_rejects_forged_program_pass_ok",
            "test_stem_only_tweak_records_cheating_flag_and_exit_code_7",
            "test_validate_trial_snapshot_record_accepts_human_review_scores",
        ),
    ),
    (
        "tests/examples/test_agent_trial_reference.py",
        ("test_snapshot_design_stem_tweak_exit_code_7",),
    ),
    (
        "tests/examples/test_agent_trial.py",
        (
            "test_snapshot_presets_script_writes_gate_baseline",
            "test_validate_snapshot_recursive_on_reference_trials",
            "test_validate_snapshot_require_human_scores_exit_8_without_scores",
            "test_validate_snapshot_script_on_reference_trial",
        ),
    ),
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
    assert "snapshot_design.py" in text
    assert "test_agent_trial_reference" in text
    assert "test_development_plan_section8" in text


def test_section8_skill_reference_documents_m5_workflow() -> None:
    """§8.7: skill reference points at trials, review bundle, and acceptance tests."""
    text = (
        ROOT / ".agents/skills/typekernel-font-design/reference.md"
    ).read_text(encoding="utf-8")
    assert "human_review_bundle" in text
    assert "snapshot_serif_voices" in text
    assert "validate_trial_snapshot" in text
    assert "validate_snapshot.py" in text
    assert "trial_snapshot_exit_code" in text
    assert "test_serif_voice_meets_tk306_program_acceptance" in text
    assert "test_italic_program_acceptance" in text
    assert "test_development_plan_section8" in text


def test_section8_agent_recipes_documents_trial_snapshot_exit_codes() -> None:
    text = (ROOT / "docs/agent-recipes.md").read_text(encoding="utf-8")
    assert "TK-502" in text
    assert "validate_trial_snapshot" in text
    assert "trial_snapshot_exit_code" in text
    assert "run_m5_program_exit" in text


def test_section8_agent_trial_readme_documents_snapshot_exit_codes() -> None:
    text = (ROOT / "examples/agent_trial/README.md").read_text(encoding="utf-8")
    assert "trial_snapshot_exit_code" in text
    assert "validate_trial_snapshot" in text
    assert "validate_snapshot.py" in text
    assert "AGENT_TRIALS.md" in text


def test_section8_skill_documents_m5_exit_workflow() -> None:
    text = (
        ROOT / ".agents/skills/typekernel-font-design/SKILL.md"
    ).read_text(encoding="utf-8")
    assert "human_review_bundle" in text
    assert "run_m5_program_exit" in text
    assert "validate_snapshot.py" in text
    assert "test_development_plan_section8" in text
    assert "test_m3_exit" in text


def test_section8_readme_points_at_plan_and_review_bundle() -> None:
    text = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "DEVELOPMENT_PLAN.md" in text
    assert "human_review_bundle.py" in text
    assert "run_m5_program_exit.py" in text
    assert "validate_snapshot.py" in text
    assert "test_development_plan_section8" in text


def test_section8_dev_standards_documents_program_exit() -> None:
    text = (ROOT / "docs/dev-standards.md").read_text(encoding="utf-8")
    assert "test_development_plan_section8" in text
    assert "run_m5_program_exit" in text
    assert "validate_snapshot.py" in text
    assert "human_review_bundle" in text
    assert "AGENT_SENTENCE" in text


def test_section8_agent_goal_documents_program_vs_human_gates() -> None:
    text = (ROOT / "docs/AGENT_GOAL.md").read_text(encoding="utf-8")
    assert "human_review_bundle" in text
    assert "run_m5_program_exit" in text
    assert "validate_snapshot.py" in text
    assert "test_serif_voice_meets_tk306_program_acceptance" in text


def test_section8_approvals_readme_documents_review_workflow() -> None:
    text = (ROOT / "approvals/README.md").read_text(encoding="utf-8")
    assert "human_review_bundle" in text
    assert "test_serif_voice_meets_tk306_program_acceptance" in text
    assert "test_development_plan_section8" in text
    for gate_file in _PENDING_HUMAN_GATES:
        assert Path(gate_file).name in text
    assert text.count("pytest -q") >= len(_PENDING_HUMAN_GATES)


def test_section8_regression_test_hooks_present() -> None:
    """§8.4–§8.5 / TK-306–402: named acceptance tests stay in the tree."""
    for rel, test_names in _SECTION8_REGRESSION_TESTS:
        path = ROOT / rel
        assert path.is_file(), rel
        text = path.read_text(encoding="utf-8")
        for name in test_names:
            assert f"def {name}" in text, f"{rel} missing {name}"


def test_section8_plan_section6_documents_trial_snapshot_fields() -> None:
    text = (ROOT / "docs/DEVELOPMENT_PLAN.md").read_text(encoding="utf-8")
    section = text.split("## 6. Agent 试验协议")[1].split("## 7.")[0]
    assert "program_pass_ok" in section
    assert "cheating_flags" in section
    assert "validate_snapshot.py" in section


def test_section8_plan_documents_program_vs_human_exit() -> None:
    """Plan §8 progress table must not claim full M5 exit while gates stay pending."""
    text = (ROOT / "docs/DEVELOPMENT_PLAN.md").read_text(encoding="utf-8")
    assert "进度对照" in text
    assert "test_known_defects" in text
    assert "test_section8_family_gate_on_main_and_serif_voices" in text
    assert "approved: false" in text
    assert "终验" in text
    assert "2.3.1 质量门禁（当前）" in text
