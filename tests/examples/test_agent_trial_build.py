"""TK-502 brief-1 reference family build smoke."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

pytest.importorskip("ufoLib2")
pytest.importorskip("ufo2ft")

ROOT = Path(__file__).resolve().parents[2]
TRIAL = ROOT / "examples" / "agent_trial"


def test_build_brief1_reference_script(tmp_path: Path) -> None:
    proc = subprocess.run(
        [sys.executable, "build_brief1_reference.py", "--out", str(tmp_path)],
        cwd=TRIAL,
        capture_output=True,
        text=True,
        check=False,
        env={**os.environ, "PYTHONPATH": str(ROOT / "src")},
    )
    assert proc.returncode == 0, proc.stderr or proc.stdout
    assert list(tmp_path.glob("*.otf"))
    assert (tmp_path / "proof.png").is_file()
    assert (tmp_path / "snapshot.json").is_file()
