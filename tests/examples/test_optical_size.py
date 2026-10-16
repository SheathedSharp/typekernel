"""Optical-size VF example smoke."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

pytest.importorskip("ufoLib2")
pytest.importorskip("ufo2ft")

ROOT = Path(__file__).resolve().parents[2]
EXAMPLE = ROOT / "examples" / "optical_size"


def test_optical_size_build_opsz_vf_script(tmp_path: Path) -> None:
    proc = subprocess.run(
        [sys.executable, "build_opsz_vf.py", "--out", str(tmp_path)],
        cwd=EXAMPLE,
        capture_output=True,
        text=True,
        check=False,
        env={**os.environ, "PYTHONPATH": str(ROOT / "src")},
    )
    assert proc.returncode == 0, proc.stderr or proc.stdout
    assert list(tmp_path.glob("*.ttf"))
    assert (tmp_path / "proof.png").is_file()
    assert (tmp_path / "proof_vf.png").is_file()
    from fontTools.ttLib import TTFont

    ttf = TTFont(next(tmp_path.glob("*.ttf")))
    tags = {a.axisTag for a in ttf["fvar"].axes}
    assert tags == {"opsz"}
