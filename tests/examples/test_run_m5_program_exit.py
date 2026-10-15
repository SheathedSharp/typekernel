"""Smoke: examples/run_m5_program_exit.py."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
_SCRIPT = ROOT / "examples" / "run_m5_program_exit.py"


def _run(*extra: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(_SCRIPT), *extra],
        capture_output=True,
        text=True,
        check=False,
        cwd=ROOT,
        env={**os.environ, "PYTHONPATH": str(ROOT / "src")},
    )


def test_run_m5_program_exit_list_includes_section8_and_gate_evidence() -> None:
    proc = _run("--list")
    assert proc.returncode == 0, proc.stderr or proc.stdout
    lines = [ln.strip() for ln in proc.stdout.splitlines() if ln.strip()]
    assert "tests/docs/test_development_plan_section8.py" in lines
    assert "tests/parts/test_serifs.py" in lines
    assert "tests/parts/test_italic_program_acceptance.py" in lines


def test_run_m5_program_exit_section8_only() -> None:
    proc = _run("--gate", "section8", "--list")
    assert proc.returncode == 0
    assert proc.stdout.strip() == "tests/docs/test_development_plan_section8.py"


def test_run_m5_program_exit_runs_section8() -> None:
    proc = _run("--gate", "section8")
    assert proc.returncode == 0, proc.stderr or proc.stdout
