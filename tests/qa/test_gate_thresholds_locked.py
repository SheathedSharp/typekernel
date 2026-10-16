"""Frozen gate constants — change thresholds only with an explicit test update."""

from __future__ import annotations

from typekernel.qa.counter import COUNTER_SCAN_MIN_RUN_OVER_STEM
from typekernel.qa.family_gate import FAMILY_GATE_VERSION
from typekernel.qa.sentence_gate import (
    AGENT_SENTENCE,
    RELATIVE_RATIO_SLACK,
    SentenceGateLimits,
)


def test_sentence_gate_limits_frozen() -> None:
    limits = SentenceGateLimits()
    assert limits.max_optical_gap_ratio == 1.45
    assert limits.max_stem_cv == 0.15
    assert limits.max_non_terminal_g1 == 120


def test_agent_sentence_and_slack_frozen() -> None:
    assert AGENT_SENTENCE == "Ideas ship farther. Build a brighter tomorrow."
    assert RELATIVE_RATIO_SLACK == 1e-3


def test_family_gate_version_frozen() -> None:
    assert FAMILY_GATE_VERSION == "1"


def test_counter_scan_min_run_over_stem_frozen() -> None:
    assert COUNTER_SCAN_MIN_RUN_OVER_STEM == 0.09
