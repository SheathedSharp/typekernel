"""CI gate: locked sentence, preset baseline, and pair collisions."""

from __future__ import annotations

from dataclasses import replace

from typekernel.parts import Controls, DesignContext
from typekernel.parts.control import f_from_n
from typekernel.qa.sentence_gate import (
    AGENT_PAIRS,
    AGENT_SENTENCE,
    PairGap,
    check_sentence_gate,
    collect_gate_failures,
    controls_pair_gaps,
)


def test_code_clear_passes_agent_sentence_gate() -> None:
    controls = Controls.from_context(DesignContext.code_clear())
    report, failures = check_sentence_gate(controls, text=AGENT_SENTENCE)
    assert failures == (), failures
    # Pin baseline so improvements tighten limits deliberately.
    assert report.optical_gap_ratio <= 1.36
    assert report.stem_cv <= 0.06
    assert report.g1_join_error_count - report.terminal_count <= 100


def test_swapped_proof_sentence_fails() -> None:
    controls = Controls.from_context(DesignContext.code_clear())
    report, failures = check_sentence_gate(controls, text="Hi.")
    assert any("AGENT_SENTENCE" in item for item in failures)
    assert report.optical_gap_ratio <= 1.36


def test_identical_preset_baseline_passes() -> None:
    controls = Controls.from_context(DesignContext.humanist_sans())
    report, failures = check_sentence_gate(controls, baseline=controls)
    assert failures == (), failures
    # Pin the preset the way code_clear is pinned, so a "trial" cannot
    # quietly move the floor it is compared against.
    assert report.optical_gap_ratio <= 1.39
    assert report.g1_join_error_count - report.terminal_count <= 100


def test_untethered_tune_is_worse_than_humanist_preset() -> None:
    """The agent-studio anti-pattern: free floats, one glyph, worse than the preset."""
    ctx = replace(
        DesignContext.humanist_sans().tuned(
            stem=78.0,
            x_height=520.0,
            tracking=2.0,
            aperture=0.68,
            sidebearing_ratio=0.09,
        ),
        terminal_style="angled",
    )
    trial = Controls.from_context(ctx)
    trial = trial.tuned_n(counter=trial.n.counter * 1.06)
    trial = trial.tuned_o(rx=trial.o.rx * 1.03, ry=trial.o.ry * 1.02)
    trial = trial.with_glyph("f", lambda n, o, c: f_from_n(n, c, arm=0.90))
    _report, failures = check_sentence_gate(
        trial,
        baseline=Controls.from_context(DesignContext.humanist_sans()),
    )
    assert any("preset baseline" in item for item in failures)


def test_preset_pairs_do_not_collide() -> None:
    for name in ("code_clear", "humanist_sans"):
        pairs = controls_pair_gaps(Controls.from_context(getattr(DesignContext, name)()))
        assert tuple(pair.text for pair in pairs) == AGENT_PAIRS
        assert all(pair.min_gap > 0.0 for pair in pairs)


def test_pair_collision_is_a_failure() -> None:
    controls = Controls.from_context(DesignContext.code_clear())
    report, _failures = check_sentence_gate(controls)
    failures = collect_gate_failures(
        report,
        pairs=(PairGap("Ta", (-4.0,), -4.0),),
    )
    assert any("collides" in item for item in failures)
