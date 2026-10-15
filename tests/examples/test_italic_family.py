"""M4 italic_family example: wght×ital VF smoke."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

pytest.importorskip("ufoLib2")
pytest.importorskip("ufo2ft")

ROOT = Path(__file__).resolve().parents[2]
EXAMPLE = ROOT / "examples" / "italic_family"


def test_italic_family_build_vf_script(tmp_path: Path) -> None:
    proc = subprocess.run(
        [sys.executable, "build_italic_vf.py", "--out", str(tmp_path)],
        cwd=EXAMPLE,
        capture_output=True,
        text=True,
        check=False,
        env={**os.environ, "PYTHONPATH": str(ROOT / "src")},
    )
    assert proc.returncode == 0, proc.stderr or proc.stdout
    assert list(tmp_path.glob("*.ttf"))
