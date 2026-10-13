"""CI gate: agent sentence on default Controls pipeline."""

from __future__ import annotations

from typekernel.parts import Controls, DesignContext
from typekernel.qa.sentence_gate import AGENT_SENTENCE, check_sentence_gate


def test_code_clear_passes_agent_sentence_gate() -> None:
    controls = Controls.from_context(DesignContext.code_clear())
    report, failures = check_sentence_gate(controls, text=AGENT_SENTENCE)
    assert failures == (), failures
    # Pin baseline so improvements tighten limits deliberately.
    assert report.optical_gap_ratio <= 1.36
    assert report.stem_cv <= 0.06
    assert report.g1_join_error_count - report.terminal_count <= 100
