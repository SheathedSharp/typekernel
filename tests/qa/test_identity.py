"""Glyph identity rules."""

from __future__ import annotations

from typekernel.parts import DesignContext, FormSources
from typekernel.qa.identity import check_identity_controls

_PRESETS = (
    "humanist_sans",
    "geometric_sans",
    "code_clear",
    "mono",
    "paper_ink",
)


def test_exclam_ok_on_humanist() -> None:
    report = check_identity_controls(
        FormSources.from_context(DesignContext.humanist_sans()),
        "!",
    )
    assert report.ok()


def test_question_ok_on_humanist() -> None:
    report = check_identity_controls(
        FormSources.from_context(DesignContext.humanist_sans()),
        "?",
    )
    assert report.ok()


def test_currency_punct_ok_on_humanist() -> None:
    c = FormSources.from_context(DesignContext.humanist_sans())
    for ch in "&#$%":
        report = check_identity_controls(c, ch)
        assert report.ok(), ch


def test_core_letters_ok_on_presets() -> None:
    good = "abcdeoHOA"
    for name in _PRESETS:
        report = check_identity_controls(
            FormSources.from_context(getattr(DesignContext, name)()),
            good,
        )
        assert report.ok(), (name, report.errors)
