"""Registered charset defects (strict xfail until M2 fixes land)."""

from __future__ import annotations

import pytest

from typekernel.geo.outline import bounds
from typekernel.parts import Controls, DesignContext
from typekernel.qa.identity import check_identity_glyph
from typekernel.qa.lint import lint_controls, lint_glyph

_CTX = DesignContext.humanist_sans()
_CONTROLS = Controls.from_context(_CTX)


def _glyph(ch: str):
    return _CONTROLS.build_all(ch)[ch]


def test_b01_exclam() -> None:
    issues = check_identity_glyph(_glyph("!"), _CTX, glyph_name="!")
    assert not issues


def test_b02_question() -> None:
    issues = check_identity_glyph(_glyph("?"), _CTX, glyph_name="?")
    assert not issues


def test_b03_ampersand() -> None:
    issues = check_identity_glyph(_glyph("&"), _CTX, glyph_name="&")
    assert not issues


def test_b04_hash() -> None:
    issues = check_identity_glyph(_glyph("#"), _CTX, glyph_name="#")
    assert not issues


def test_b05_dollar() -> None:
    issues = check_identity_glyph(_glyph("$"), _CTX, glyph_name="$")
    assert not issues


def test_b06_percent() -> None:
    issues = check_identity_glyph(_glyph("%"), _CTX, glyph_name="%")
    assert not issues


def test_b08_equals_keyhole() -> None:
    issues = lint_glyph(_glyph("="), _CTX, glyph_name="=")
    assert not any(i.rule == "R2_keyhole" for i in issues)


def test_b09_m_crotch_no_keyhole() -> None:
    issues = lint_glyph(_glyph("m"), _CTX, glyph_name="m")
    assert not any(i.rule == "R2_keyhole" for i in issues)


@pytest.mark.xfail(strict=True, reason="B-09 m thickness above control band until calibrated")
def test_b09_m_thickness_band() -> None:
    report = lint_controls(_CONTROLS, "m", thickness=True)
    assert not any(i.rule == "R9_thickness_outlier" for i in report.issues)


def test_b10_u_flat_baseline() -> None:
    assert bounds(_glyph("u").solids[0])[1] == 0.0
