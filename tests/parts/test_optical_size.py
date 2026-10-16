"""Optical-size context deltas (opsz text ↔ display)."""

from __future__ import annotations

import pytest

from typekernel.parts import Controls, DesignContext, context_for_opsz
from typekernel.parts.optical_size import DEFAULT_DISPLAY_OPSZ, DEFAULT_TEXT_OPSZ


def test_context_for_opsz_text_heavier_than_display() -> None:
    base = DesignContext.code_clear()
    text = context_for_opsz(base, DEFAULT_TEXT_OPSZ)
    display = context_for_opsz(base, DEFAULT_DISPLAY_OPSZ)
    assert text.stem > display.stem
    assert text.tracking < display.tracking
    assert text.overshoot < display.overshoot
    assert text.aperture >= display.aperture


def test_context_for_opsz_endpoints_clamp() -> None:
    base = DesignContext.humanist_sans()
    below = context_for_opsz(base, 8.0)
    text = context_for_opsz(base, DEFAULT_TEXT_OPSZ)
    assert below.stem == pytest.approx(text.stem)
    above = context_for_opsz(base, 120.0)
    display = context_for_opsz(base, DEFAULT_DISPLAY_OPSZ)
    assert above.stem == pytest.approx(display.stem)


def test_context_for_opsz_midpoint_lerps() -> None:
    base = DesignContext.code_clear()
    text = context_for_opsz(base, DEFAULT_TEXT_OPSZ)
    display = context_for_opsz(base, DEFAULT_DISPLAY_OPSZ)
    mid = context_for_opsz(base, 43.0)  # midpoint of 14..72
    assert text.stem > mid.stem > display.stem


def test_opsz_masters_build_same_charset() -> None:
    base = DesignContext.code_clear()
    text = Controls.from_context(context_for_opsz(base, DEFAULT_TEXT_OPSZ))
    display = Controls.from_context(context_for_opsz(base, DEFAULT_DISPLAY_OPSZ))
    assert set(text.build_all()) == set(display.build_all())
