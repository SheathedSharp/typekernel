"""TracyInkPlugin — scanline ink-density suggestions."""

from __future__ import annotations

from pathlib import Path

from typekernel.plugins.spacing import TracyInkPlugin, run_spacing_plugin
from typekernel.project import open_project


def test_tracy_ink_plugin_on_latin_sans() -> None:
    root = Path(__file__).resolve().parents[3] / "src/typekernel/starters/latin_sans"
    with open_project(root) as session:
        suggestions = run_spacing_plugin(
            session, TracyInkPlugin(), names=("n", "o")
        )
    by = {s.glyph: s for s in suggestions.sidebearings}
    assert set(by) == {"n", "o"}
    assert by["n"].method == "tracy_ink"
    assert "ink fraction" in by["n"].note.lower() or "scanline" in by["n"].note.lower()
    assert by["n"].lsb >= 0.0
