"""Smoke: examples/diff_overlay.py (TK-104 review helper)."""

from __future__ import annotations

import importlib.util
import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
_SCRIPT = ROOT / "examples" / "diff_overlay.py"

pytestmark = pytest.mark.skipif(
    importlib.util.find_spec("PIL") is None,
    reason="diff overlay needs Pillow",
)


def test_diff_overlay_script_writes_png(tmp_path: Path) -> None:
    out = tmp_path / "diff.png"
    proc = subprocess.run(
        [
            sys.executable,
            str(_SCRIPT),
            "--trial-preset",
            "slab_serif",
            "--baseline-preset",
            "humanist_sans",
            "--chars",
            "m",
            "--out",
            str(out),
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
        env={**os.environ, "PYTHONPATH": str(ROOT / "src")},
    )
    assert proc.returncode == 0, proc.stderr or proc.stdout
    assert out.is_file()
    assert out.stat().st_size > 200
