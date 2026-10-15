"""Agent trial snapshot scripts (TK-502)."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TRIAL = ROOT / "examples" / "agent_trial"


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
