"""TK-502 reference family build smoke (Regular + Bold per brief)."""

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


@pytest.mark.parametrize("brief_id", ("brief-1", "brief-2", "brief-3"))
def test_build_reference_family_script(tmp_path: Path, brief_id: str) -> None:
    proc = subprocess.run(
        [
            sys.executable,
            "build_reference_family.py",
            "--brief",
            brief_id,
            "--out",
            str(tmp_path / brief_id),
        ],
        cwd=TRIAL,
        capture_output=True,
        text=True,
        check=False,
        env={**os.environ, "PYTHONPATH": str(ROOT / "src")},
    )
    assert proc.returncode == 0, proc.stderr or proc.stdout
    out = tmp_path / brief_id
    assert list(out.glob("*.otf"))
    assert (out / "proof.png").is_file()
    assert (out / "snapshot.json").is_file()
