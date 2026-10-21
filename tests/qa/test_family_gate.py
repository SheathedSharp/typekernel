"""Charset-wide family gate."""

from __future__ import annotations

import pytest

from typekernel.parts import DesignContext, FormSources
from typekernel.qa.family_gate import (
    FAMILY_GATE_VERSION,
    check_family_gate,
    collect_family_gate_failures,
)


def test_version_locked() -> None:
    assert FAMILY_GATE_VERSION == "1"


_PRESETS = (
    "humanist_sans",
    "geometric_sans",
    "code_clear",
    "mono",
    "display",
    "paper_ink",
    "open_print",
)

# DEVELOPMENT_PLAN §8.3: main sans presets + TK-306 serif voices.
_SECTION8_GATE_PRESETS = (
    "humanist_sans",
    "geometric_sans",
    "code_clear",
    "slab_serif",
    "bracketed_serif",
)


@pytest.mark.parametrize("preset", _PRESETS)
def test_preset_passes_family_gate(preset: str) -> None:
    failures = collect_family_gate_failures(
        FormSources.from_context(getattr(DesignContext, preset)())
    )
    assert not failures, failures


@pytest.mark.parametrize("preset", _SECTION8_GATE_PRESETS)
def test_section8_family_gate_on_main_and_serif_voices(preset: str) -> None:
    failures = collect_family_gate_failures(
        FormSources.from_context(getattr(DesignContext, preset)())
    )
    assert not failures, failures


def test_check_family_gate_multiple_masters() -> None:
    ctx = DesignContext.humanist_sans()
    regular = FormSources.from_context(ctx)
    bold = FormSources.from_context(ctx.tuned(stem=140.0)).with_stem_relief()
    failures = check_family_gate(regular, masters=(regular, bold))
    assert not failures, failures
