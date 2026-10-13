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
