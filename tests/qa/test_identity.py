"""Glyph identity rules."""

from __future__ import annotations

from typekernel.parts import Controls, DesignContext
from typekernel.qa.identity import check_identity_controls

_PRESETS = (
    "humanist_sans",
    "geometric_sans",
    "code_clear",
    "mono",
    "paper_ink",
)


def test_exclam_fails_on_humanist() -> None:
    report = check_identity_controls(
        Controls.from_context(DesignContext.humanist_sans()),
        "!",
    )
    assert not report.ok()
    assert any(i.glyph == "!" for i in report.errors)


def test_ampersand_fails_on_humanist() -> None:
    report = check_identity_controls(
        Controls.from_context(DesignContext.humanist_sans()),
        "&",
    )
    assert not report.ok()


def test_hash_and_percent_fail() -> None:
    c = Controls.from_context(DesignContext.humanist_sans())
    for ch in "#%":
        report = check_identity_controls(c, ch)
        assert not report.ok(), ch


def test_dollar_fails_counters() -> None:
    report = check_identity_controls(
        Controls.from_context(DesignContext.humanist_sans()),
        "$",
    )
    assert not report.ok()


def test_core_letters_ok_on_presets() -> None:
    good = "abcdeoHOA"
    for name in _PRESETS:
        report = check_identity_controls(
            Controls.from_context(getattr(DesignContext, name)()),
            good,
        )
        assert report.ok(), (name, report.errors)
