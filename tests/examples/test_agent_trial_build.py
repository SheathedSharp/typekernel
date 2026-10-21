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
TRIAL = ROOT / "examples" / "_legacy" / "agent_trial"


@pytest.mark.parametrize(
    ("brief_id", "variant"),
    (
        ("brief-1", None),
        ("brief-2", None),
        ("brief-2", "slab"),
        ("brief-2", "bracketed"),
        ("brief-3", None),
    ),
)
def test_build_reference_family_script(
    tmp_path: Path, brief_id: str, variant: str | None
) -> None:
    cmd = [
        sys.executable,
        "build_reference_family.py",
        "--brief",
        brief_id,
        "--out",
        str(tmp_path / f"{brief_id}-{variant or 'default'}"),
    ]
    if variant:
        cmd.extend(["--variant", variant])
    proc = subprocess.run(
        cmd,
        cwd=TRIAL,
        capture_output=True,
        text=True,
        check=False,
        env={**os.environ, "PYTHONPATH": str(ROOT / "src")},
    )
    assert proc.returncode == 0, proc.stderr or proc.stdout
    out = tmp_path / f"{brief_id}-{variant or 'default'}"
    assert list(out.glob("*.otf"))
    assert (out / "proof.png").is_file()
    assert (out / "snapshot.json").is_file()
