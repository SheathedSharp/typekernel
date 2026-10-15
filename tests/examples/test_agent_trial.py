"""Agent trial snapshot scripts (TK-502)."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

from typekernel.qa.trial_protocol import (
    trial_snapshot_json_exit_code,
    validate_trial_snapshot_record,
)

ROOT = Path(__file__).resolve().parents[2]
TRIAL = ROOT / "examples" / "agent_trial"


def test_snapshot_presets_script_writes_gate_baseline(tmp_path: Path) -> None:
    proc = subprocess.run(
        [sys.executable, "snapshot_presets.py", "--out", str(tmp_path)],
        cwd=TRIAL,
        capture_output=True,
        text=True,
        check=False,
        env={**os.environ, "PYTHONPATH": str(ROOT / "src")},
    )
    assert proc.returncode == 0, proc.stderr or proc.stdout
    for brief_id in ("brief-1", "brief-2", "brief-3"):
        data = json.loads((tmp_path / brief_id / "snapshot.json").read_text(encoding="utf-8"))
        assert data["family_gate_ok"] is True
        assert data["cheating_flags"] == []
        assert data["program_pass_ok"] is False
        assert data["l3_voice_ok"] is False
        problems = validate_trial_snapshot_record(data)
        assert not problems
        assert trial_snapshot_json_exit_code(data, problems) == 6


def test_snapshot_serif_voices_script(tmp_path: Path) -> None:
    proc = subprocess.run(
        [sys.executable, "snapshot_serif_voices.py", "--out", str(tmp_path)],
        cwd=TRIAL,
        capture_output=True,
        text=True,
        check=False,
        env={**os.environ, "PYTHONPATH": str(ROOT / "src")},
    )
    assert proc.returncode == 0, proc.stderr or proc.stdout
    for voice in ("slab_serif", "bracketed_serif"):
        snap = tmp_path / voice / "snapshot.json"
        assert snap.is_file()
        data = json.loads(snap.read_text(encoding="utf-8"))
        assert data["family_gate_ok"] is True
        assert data["l3_voice_ok"] is True
        assert data["program_pass_ok"] is True
        problems = validate_trial_snapshot_record(data)
        assert not problems
    proc = subprocess.run(
        [
            sys.executable,
            "validate_snapshot.py",
            str(tmp_path / "slab_serif"),
            str(tmp_path / "bracketed_serif"),
        ],
        cwd=TRIAL,
        capture_output=True,
        text=True,
        check=False,
        env={**os.environ, "PYTHONPATH": str(ROOT / "src")},
    )
    assert proc.returncode == 0, proc.stderr or proc.stdout


def test_validate_snapshot_recursive_on_reference_trials(tmp_path: Path) -> None:
    subprocess.run(
        [
            sys.executable,
            "snapshot_reference_trials.py",
            "--out",
            str(tmp_path),
        ],
        cwd=TRIAL,
        capture_output=True,
        text=True,
        check=True,
        env={**os.environ, "PYTHONPATH": str(ROOT / "src")},
    )
    proc = subprocess.run(
        [
            sys.executable,
            "validate_snapshot.py",
            "--recursive",
            str(tmp_path),
        ],
        cwd=TRIAL,
        capture_output=True,
        text=True,
        check=False,
        env={**os.environ, "PYTHONPATH": str(ROOT / "src")},
    )
    assert proc.returncode == 0, proc.stderr or proc.stdout


def test_validate_snapshot_script_on_reference_trial(tmp_path: Path) -> None:
    subprocess.run(
        [
            sys.executable,
            "snapshot_design.py",
            "--brief",
            "brief-1",
            "--design",
            "design_warm_humanist.py",
            "--out",
            str(tmp_path),
        ],
        cwd=TRIAL,
        capture_output=True,
        text=True,
        check=True,
        env={**os.environ, "PYTHONPATH": str(ROOT / "src")},
    )
    proc = subprocess.run(
        [
            sys.executable,
            "validate_snapshot.py",
            str(tmp_path / "snapshot.json"),
        ],
        cwd=TRIAL,
        capture_output=True,
        text=True,
        check=False,
        env={**os.environ, "PYTHONPATH": str(ROOT / "src")},
    )
    assert proc.returncode == 0, proc.stderr or proc.stdout
