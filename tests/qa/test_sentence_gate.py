"""CI gate: locked sentence, preset baseline, and pair collisions."""

from __future__ import annotations

from dataclasses import replace

from typekernel.parts import DesignContext, FormSources
from typekernel.qa.sentence_gate import (
    AGENT_PAIRS,
    AGENT_SENTENCE,
    PairGap,
    check_sentence_gate,
    collect_gate_failures,
    controls_pair_gaps,
)


def test_code_clear_passes_agent_sentence_gate() -> None:
    controls = FormSources.from_context(DesignContext.code_clear())
    report, failures = check_sentence_gate(controls, text=AGENT_SENTENCE)
    assert failures == (), failures
    # Pin baseline so improvements tighten limits deliberately.
    # Ratio is the class-kern residual (``ow``), not unkerned capitals.
    assert report.optical_gap_ratio <= 1.05
    assert report.stem_cv <= 0.06
    assert report.g1_join_error_count - report.terminal_count <= 105


def test_slab_serif_passes_agent_sentence_gate() -> None:
    """TK-306: slab voice must stay within locked non-terminal G1 budget."""
    controls = FormSources.from_context(DesignContext.slab_serif())
    report, failures = check_sentence_gate(controls, text=AGENT_SENTENCE)
    assert failures == (), failures
    assert report.g1_join_error_count - report.terminal_count <= 118


def test_bracketed_serif_passes_agent_sentence_gate() -> None:
    """TK-306: bracketed voice must stay within locked non-terminal G1 budget."""
    controls = FormSources.from_context(DesignContext.bracketed_serif())
    report, failures = check_sentence_gate(controls, text=AGENT_SENTENCE)
    assert failures == (), failures
    assert report.g1_join_error_count - report.terminal_count <= 118


def test_swapped_proof_sentence_fails() -> None:
    controls = FormSources.from_context(DesignContext.code_clear())
    report, failures = check_sentence_gate(controls, text="Hi.")
    assert any("AGENT_SENTENCE" in item for item in failures)
    assert report.optical_gap_ratio <= 1.05


def test_identical_preset_baseline_passes() -> None:
    controls = FormSources.from_context(DesignContext.humanist_sans())
    report, failures = check_sentence_gate(controls, baseline=controls)
    assert failures == (), failures
    # Pin the preset the way code_clear is pinned, so a "trial" cannot
    # quietly move the floor it is compared against.
    assert report.optical_gap_ratio <= 1.05
    assert report.g1_join_error_count - report.terminal_count <= 105


def test_relative_baseline_rejects_worse_ratio() -> None:
    controls = FormSources.from_context(DesignContext.humanist_sans())
    report, failures = check_sentence_gate(controls)
    assert failures == ()
    worse = replace(report, optical_gap_ratio=report.optical_gap_ratio + 0.2)
    flagged = collect_gate_failures(worse, baseline_report=report, pairs=())
    assert any("preset baseline" in item for item in flagged)


def test_preset_pairs_do_not_collide() -> None:
    for name in ("code_clear", "humanist_sans"):
        pairs = controls_pair_gaps(FormSources.from_context(getattr(DesignContext, name)()))
        assert tuple(pair.text for pair in pairs) == AGENT_PAIRS
        assert all(pair.min_gap > 0.0 for pair in pairs)


def test_pair_collision_is_a_failure() -> None:
    controls = FormSources.from_context(DesignContext.code_clear())
    report, _failures = check_sentence_gate(controls)
    failures = collect_gate_failures(
        report,
        pairs=(PairGap("Ta", (-4.0,), -4.0),),
    )
    assert any("collides" in item for item in failures)
