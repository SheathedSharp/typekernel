"""Smoke: examples/regenerate_outline_hashes.py (TK-108)."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
_SCRIPT = ROOT / "examples" / "regenerate_outline_hashes.py"


def test_regenerate_outline_hashes_check_passes() -> None:
    proc = subprocess.run(
        [sys.executable, str(_SCRIPT)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
        env={**os.environ, "PYTHONPATH": str(ROOT / "src")},
    )
    assert proc.returncode == 0, proc.stderr or proc.stdout
