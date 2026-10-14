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


def test_humanist_preset_has_charset_failures() -> None:
    failures = collect_family_gate_failures(
        Controls.from_context(DesignContext.humanist_sans())
    )
    assert failures
    assert any(
        ch in f for ch in ('"', "'", "\u2019", "\u201d") for f in failures
    )


def test_check_family_gate_multiple_masters() -> None:
    ctx = DesignContext.humanist_sans()
    regular = Controls.from_context(ctx)
    bold = Controls.from_context(ctx.tuned(stem=140.0)).with_stem_relief()
    failures = check_family_gate(regular, masters=(regular, bold))
    assert failures
    assert any("stem=70" in f for f in failures)
    assert any("stem=140" in f for f in failures)
