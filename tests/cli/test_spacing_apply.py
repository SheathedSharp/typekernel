"""tk spacing apply: dry-run default; --write opt-in Abs rewrite."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

from typekernel.cli.spacing_cmd import spacing_apply, spacing_suggest


def _copy_latin(tmp_path: Path) -> Path:
    src = Path(__file__).resolve().parents[2] / "src/typekernel/starters/latin_sans"
    root = tmp_path / "latin_sans"
    shutil.copytree(src, root)
    return root


def test_tk_spacing_apply_dry_run(tmp_path: Path) -> None:
    root = _copy_latin(tmp_path)
    before = (root / "spacing.py").read_text(encoding="utf-8")
    out = tmp_path / "plan.json"
    written = spacing_apply(
        root, out=out, plugin="bbox_rhythm", names=["n", "o"], write=False
    )
    assert written == out
    assert (root / "spacing.py").read_text(encoding="utf-8") == before
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert payload["dry_run"] is True


def test_tk_spacing_apply_write(tmp_path: Path) -> None:
    root = _copy_latin(tmp_path)
    out = tmp_path / "plan.json"
    spacing_apply(root, out=out, plugin="optical_air", names=["n"], write=True)
    text = (root / "spacing.py").read_text(encoding="utf-8")
    assert "Abs(" in text
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert payload["dry_run"] is False


def test_tk_spacing_suggest_tracy_bands(tmp_path: Path) -> None:
    src = Path(__file__).resolve().parents[2] / "src/typekernel/starters/latin_sans"
    out = tmp_path / "sug.json"
    written = spacing_suggest(
        src, out=out, plugin="tracy_bands", names=["n", "o"]
    )
    payload = json.loads(written.read_text(encoding="utf-8"))
    assert payload["plugin"] == "tracy_bands"
    assert len(payload["sidebearings"]) == 2
