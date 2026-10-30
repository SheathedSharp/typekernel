"""TracyBandPlugin — multi-band silhouette suggestions; optional kern pairs."""

from __future__ import annotations

from pathlib import Path

from typekernel.plugins.spacing import TracyBandPlugin, run_spacing_plugin
from typekernel.project import open_project


def test_tracy_band_plugin_on_latin_sans() -> None:
    root = Path(__file__).resolve().parents[3] / "src/typekernel/starters/latin_sans"
    with open_project(root) as session:
        suggestions = run_spacing_plugin(
            session, TracyBandPlugin(), names=("n", "o")
        )
    assert suggestions.pairs == ()
    by = {s.glyph: s for s in suggestions.sidebearings}
    assert set(by) == {"n", "o"}
    assert by["n"].method == "tracy_bands"
    assert "not gray-value" in by["n"].note.lower() or "not gray" in by["n"].note.lower()
    assert by["n"].lsb >= 0.0


def test_tracy_band_plugin_optional_pairs() -> None:
    root = Path(__file__).resolve().parents[3] / "src/typekernel/starters/latin_sans"
    with open_project(root) as session:
        suggestions = run_spacing_plugin(
            session, TracyBandPlugin(include_pairs=True), names=("n",)
        )
    # pairs may be empty if no seed gaps need kern — just ensure delegation path runs
    assert isinstance(suggestions.pairs, tuple)
    for p in suggestions.pairs:
        assert p.method == "kern_suggest"
