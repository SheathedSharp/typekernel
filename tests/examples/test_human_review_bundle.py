"""Smoke: human review artifact bundle (TK-306 / TK-402)."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_human_review_bundle_serif_only(tmp_path: Path) -> None:
    proc = subprocess.run(
        [
            sys.executable,
            str(ROOT / "examples" / "human_review_bundle.py"),
            "--only",
            "serif",
            "--out",
            str(tmp_path),
        ],
        capture_output=True,
        text=True,
        check=False,
        env={**os.environ, "PYTHONPATH": str(ROOT / "src")},
    )
    assert proc.returncode == 0, proc.stderr or proc.stdout
    assert (tmp_path / "REVIEW_CHECKLIST.md").is_file()
    assert (tmp_path / "slab_serif" / "proof.png").is_file()
    assert (tmp_path / "bracketed_serif" / "proof.png").is_file()
    assert (tmp_path / "weight_ladder_slab_serif.png").is_file()
    assert (tmp_path / "weight_ladder_bracketed_serif.png").is_file()
    assert (tmp_path / "slab_serif_vf" / "proof_vf.png").is_file()
    assert (tmp_path / "bracketed_serif_vf" / "proof_vf.png").is_file()
    checklist = (tmp_path / "REVIEW_CHECKLIST.md").read_text(encoding="utf-8")
    assert "serif-slab-voice" in checklist
    assert "serif-bracketed-voice" in checklist


def test_human_review_bundle_italic_only(tmp_path: Path) -> None:
    proc = subprocess.run(
        [
            sys.executable,
            str(ROOT / "examples" / "human_review_bundle.py"),
            "--only",
            "italic",
            "--out",
            str(tmp_path),
        ],
        capture_output=True,
        text=True,
        check=False,
        env={**os.environ, "PYTHONPATH": str(ROOT / "src")},
    )
    assert proc.returncode == 0, proc.stderr or proc.stdout
    assert (tmp_path / "REVIEW_CHECKLIST.md").is_file()
    assert list((tmp_path / "italic_family").glob("*.ttf"))
    checklist = (tmp_path / "REVIEW_CHECKLIST.md").read_text(encoding="utf-8")
    assert "italic-vf-construct" in checklist
    assert "TK-402" in checklist
