"""Smoke: human review artifact bundle (TK-306 / TK-402)."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
_BUNDLE_SOURCE = ROOT / "examples" / "human_review_bundle.py"
_PENDING_GATES = (
    "serif-slab-voice.json",
    "serif-bracketed-voice.json",
    "italic-vf-construct.json",
)


def test_human_review_bundle_source_documents_pending_gates() -> None:
    text = _BUNDLE_SOURCE.read_text(encoding="utf-8")
    assert "serif-slab-voice" in text
    assert "serif-bracketed-voice" in text
    assert "italic-vf-construct" in text
    assert "proof_vf.png" in text
    assert "test_serif_voice_meets_tk306_program_acceptance" in text
    assert "test_italic_program_acceptance.py" in text
    assert "test_development_plan_section8.py" in text
    assert "test_agent_trial_reference.py" in text
    assert "run_m5_program_exit.py" in text
    assert "test_m3_exit.py" in text
    assert "weight_ladder_sheet.py" in text
    assert "test_weight_ladder_sheet.py" in text
    assert "tk206_s_opening_humanist.png" in text
    assert "tk206_three_g_humanist.png" in text
    assert "test_b13_three_no_flat_top_shelf" in text
    assert "test_b14_g_spur_cubic_join" in text
    assert "test_b15_s_spine_ink_is_continuous_band" in text
    assert "test_s_opening_reach_relief_frozen" in text
    assert "test_descender_micro_sliver_below_min_run_gap_ignored" in text
    assert "regenerate_outline_hashes.py" in text


def test_human_review_bundle_checklist_matches_approval_test_evidence() -> None:
    """REVIEW_CHECKLIST write_approval examples stay aligned with approvals/*.json."""
    text = _BUNDLE_SOURCE.read_text(encoding="utf-8")
    for name in _PENDING_GATES:
        evidence = load_approval_evidence(ROOT / "approvals" / name)
        for rel in evidence:
            assert rel in text, f"{name} test_evidence {rel!r} missing from human_review_bundle.py"


def load_approval_evidence(path: Path) -> list[str]:
    data = json.loads(path.read_text(encoding="utf-8"))
    raw = data.get("test_evidence", [])
    if isinstance(raw, list):
        return [str(x) for x in raw]
    raise TypeError(f"expected list test_evidence in {path.name}")


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


def test_human_review_bundle_tk206_only(tmp_path: Path) -> None:
    proc = subprocess.run(
        [
            sys.executable,
            str(ROOT / "examples" / "human_review_bundle.py"),
            "--only",
            "tk206",
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
    assert (tmp_path / "tk206_three_g_humanist.png").is_file()
    assert (tmp_path / "tk206_s_opening_humanist.png").is_file()
    checklist = (tmp_path / "REVIEW_CHECKLIST.md").read_text(encoding="utf-8")
    assert "TK-206" in checklist
    assert "tk206_s_opening_humanist.png" in checklist


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
    assert (tmp_path / "italic_family" / "proof.png").is_file()
    assert (tmp_path / "italic_family" / "proof_vf.png").is_file()
    checklist = (tmp_path / "REVIEW_CHECKLIST.md").read_text(encoding="utf-8")
    assert "italic-vf-construct" in checklist
    assert "TK-402" in checklist
