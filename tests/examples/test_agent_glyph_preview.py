"""Agent preview proof helper (requires agent-authored Controls)."""

from __future__ import annotations

from pathlib import Path

import pytest

pytest.importorskip("ufoLib2")
pytest.importorskip("PIL")

from typekernel.parts import Controls, DesignContext
from typekernel.qa.agent_preview import build_glyph_preview


def test_build_glyph_preview_writes_otf_and_pngs(tmp_path: Path) -> None:
    controls = Controls.from_context(DesignContext.code_clear())
    paths = build_glyph_preview(
        controls,
        family="Preview Test",
        focus="fI.",
        sentence="If.",
        out_dir=tmp_path,
    )
    assert paths["otf"].is_file() and paths["otf"].stat().st_size > 1000
    assert paths["grid"].is_file()
    assert paths["sentence"].is_file()
