"""Smoke: examples/weight_ladder_sheet.py (TK-207 human review helper)."""

from __future__ import annotations

import importlib.util
import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
_SCRIPT = ROOT / "examples" / "weight_ladder_sheet.py"

pytestmark = pytest.mark.skipif(
    importlib.util.find_spec("pathops") is None
    or importlib.util.find_spec("PIL") is None
    or importlib.util.find_spec("ufo2ft") is None,
    reason="weight ladder sheet needs pathops, Pillow, and compile extra",
)


def test_weight_ladder_sheet_script_writes_png(tmp_path: Path) -> None:
    out = tmp_path / "ladder.png"
    proc = subprocess.run(
        [
            sys.executable,
            str(_SCRIPT),
            "--preset",
            "humanist_sans",
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
    assert out.stat().st_size > 0
