"""kern suggest writes suggestions; does not mutate project kerning."""

from __future__ import annotations

import json
from pathlib import Path

from typekernel.cli.kern_cmd import kern_suggest
from typekernel.font.kerning import ClassKernPair, KernClass, KernPair
from typekernel.metrics import Kerning
from typekernel.metrics.kern_suggest import suggest_kern_pairs
from typekernel.project import open_project


def test_suggest_kern_pairs_returns_suggestions() -> None:
    root = Path(__file__).resolve().parents[2] / "src/typekernel/starters/latin_sans"
    with open_project(root) as session:
        suggestions = suggest_kern_pairs(session, target_gap=24.0)
    assert isinstance(suggestions, list)
    # Suggestions are data; project kerning unchanged by suggest itself.
    with open_project(root) as session:
        before = session.project.kerning
        suggest_kern_pairs(session)
        assert session.project.kerning is before


def test_tk_kern_suggest_writes_json(tmp_path: Path) -> None:
    root = Path(__file__).resolve().parents[2] / "src/typekernel/starters/latin_sans"
    out = tmp_path / "kerning-suggestions.json"
    written = kern_suggest(root, out=out)
    assert written == out
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert "pairs" in payload
    assert "not auto-applied" in payload["note"].lower() or "Not auto-applied" in payload["note"]


def test_latin_sans_kerning_has_classes() -> None:
    root = Path(__file__).resolve().parents[2] / "src/typekernel/starters/latin_sans"
    with open_project(root) as session:
        kerning = session.project.kerning
    assert kerning is not None
    assert isinstance(kerning, Kerning)
    assert len(kerning.classes) >= 1
    assert all(isinstance(c, KernClass) for c in kerning.classes)
    assert any(isinstance(p, ClassKernPair) for p in kerning.pairs) or any(
        isinstance(p, KernPair) for p in kerning.pairs
    )
