"""Feature-safe family assembly."""

from __future__ import annotations

from pathlib import Path

import pytest

pytest.importorskip("ufoLib2")

from typekernel.compile import FamilyBuildOptions, build_font, compose_font_from_controls
from typekernel.parts import Controls, DesignContext


def test_compose_liga_only_builds(tmp_path: Path) -> None:
    controls = Controls.from_context(DesignContext.code_clear())
    font = compose_font_from_controls(
        controls,
        "Gate Test",
        options=FamilyBuildOptions(liga=True),
    )
    assert "fi" in font
    assert "sub f i by fi" in font.features
    assert "zero.tf" not in font.features
    build_font(font, tmp_path, formats=("otf",))


def test_compose_requires_body_unlock_by_default() -> None:
    """Stock sheets pass the gate; a thinned body letter must refuse compose."""
    from typekernel.qa.design_sequence import DesignSequenceError

    good = Controls.from_context(DesignContext.geometric_sans())
    font = compose_font_from_controls(good, "Unlocked")
    assert "n" in font

    # Bypass stock derivation: inject a conspicuously thin ``h`` master.
    thin = Controls.from_context(DesignContext.geometric_sans().tuned(stem=35.0))
    broken = good.with_glyph("h", lambda _n, _o, _ctx: thin.build("h"))
    with pytest.raises(DesignSequenceError, match="body DesignSequence"):
        compose_font_from_controls(broken, "Blocked")


def test_compose_allow_skip_unlock_for_stock_compile() -> None:
    controls = Controls.from_context(DesignContext.code_clear())
    font = compose_font_from_controls(
        controls,
        "SkipGate",
        options=FamilyBuildOptions(liga=True),
        require_body_unlock=False,
    )
    assert "fi" in font
