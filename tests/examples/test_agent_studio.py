"""Agent studio scaffold runs when design.py is importable."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

pytest.importorskip("ufoLib2")
pytest.importorskip("PIL")

ROOT = Path(__file__).resolve().parents[2]
STUDIO = ROOT / "examples" / "agent_studio"


def test_agent_studio_build_script(tmp_path: Path) -> None:
    proc = subprocess.run(
        [sys.executable, "build.py", "--out", str(tmp_path)],
        cwd=STUDIO,
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr or proc.stdout
    assert "sentence gate ok" in proc.stdout
    assert (tmp_path / "grid.png").is_file()
    assert (tmp_path / "sentence.png").is_file()
    assert (tmp_path / "sentence_brief.png").is_file()
    assert (tmp_path / "review" / "review.json").is_file()
    assert (tmp_path / "review" / "n.png").is_file()
    otf = list(tmp_path.glob("*.otf"))
    assert otf and otf[0].stat().st_size > 1000
