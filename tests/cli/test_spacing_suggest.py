"""tk spacing suggest writes JSON; does not mutate project metrics."""

from __future__ import annotations

import json
from pathlib import Path

from typekernel.cli.spacing_cmd import spacing_suggest
from typekernel.project import open_project


def test_tk_spacing_suggest_writes_json(tmp_path: Path) -> None:
    root = Path(__file__).resolve().parents[2] / "src/typekernel/starters/latin_sans"
    out = tmp_path / "spacing-suggestions.json"
    written = spacing_suggest(root, out=out, plugin="bbox_rhythm", names=["n", "o"])
    assert written == out
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert payload["plugin"] == "bbox_rhythm"
    assert "sidebearings" in payload
    assert len(payload["sidebearings"]) == 2
    with open_project(root) as session:
        assert session.project.metrics is not None
    # suggest must not have rewritten on-disk spacing / project files
    assert (root / "project.py").exists()
    assert (root / "spacing.py").exists()
