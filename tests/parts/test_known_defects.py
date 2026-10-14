"""Registered charset defects (strict xfail until M2 fixes land)."""

from __future__ import annotations

import pytest

from typekernel.parts import Controls, DesignContext
from typekernel.qa.identity import check_identity_glyph
from typekernel.qa.lint import lint_glyph

_CTX = DesignContext.humanist_sans()
_CONTROLS = Controls.from_context(_CTX)


def _glyph(ch: str):
    return _CONTROLS.build_all(ch)[ch]


@pytest.mark.xfail(strict=True, reason="B-01 exclamation dot above stem")
def test_b01_exclam() -> None:
    issues = check_identity_glyph(_glyph("!"), _CTX, glyph_name="!")
    assert not issues


@pytest.mark.xfail(strict=True, reason="B-03 ampersand reads as e")
def test_b03_ampersand() -> None:
    issues = check_identity_glyph(_glyph("&"), _CTX, glyph_name="&")
    assert not issues


@pytest.mark.xfail(strict=True, reason="B-04 hash is a plus")
def test_b04_hash() -> None:
    issues = check_identity_glyph(_glyph("#"), _CTX, glyph_name="#")
    assert not issues


@pytest.mark.xfail(strict=True, reason="B-05 dollar missing S loops")
def test_b05_dollar() -> None:
    issues = check_identity_glyph(_glyph("$"), _CTX, glyph_name="$")
    assert not issues


@pytest.mark.xfail(strict=True, reason="B-06 percent uses dots")
def test_b06_percent() -> None:
    issues = check_identity_glyph(_glyph("%"), _CTX, glyph_name="%")
    assert not issues


@pytest.mark.xfail(strict=True, reason="B-08 equals keyhole contour")
def test_b08_equals_keyhole() -> None:
    issues = lint_glyph(_glyph("="), _CTX, glyph_name="=")
    assert not any(i.rule == "R2_keyhole" for i in issues)
