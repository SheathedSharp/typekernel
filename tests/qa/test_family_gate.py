"""Charset-wide family gate."""

from __future__ import annotations

from typekernel.parts import Controls, DesignContext
from typekernel.qa.family_gate import (
    FAMILY_GATE_VERSION,
    check_family_gate,
    collect_family_gate_failures,
)


def test_version_locked() -> None:
    assert FAMILY_GATE_VERSION == "1"


def test_humanist_preset_passes_family_gate() -> None:
    failures = collect_family_gate_failures(
        Controls.from_context(DesignContext.humanist_sans())
    )
    assert not failures, failures


def test_check_family_gate_multiple_masters() -> None:
    ctx = DesignContext.humanist_sans()
    regular = Controls.from_context(ctx)
    bold = Controls.from_context(ctx.tuned(stem=140.0)).with_stem_relief()
    failures = check_family_gate(regular, masters=(regular, bold))
    assert not failures, failures
