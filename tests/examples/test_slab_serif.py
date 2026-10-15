"""TK-306 slab serif example: gate, build, proof artifacts."""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest

pytest.importorskip("ufoLib2")
pytest.importorskip("PIL")

ROOT = Path(__file__).resolve().parents[2]
EXAMPLE = ROOT / "examples" / "slab_serif"


def _load_design():
    spec = importlib.util.spec_from_file_location("slab_serif_design", EXAMPLE / "design.py")
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_slab_preset_stems_order_light_regular_bold() -> None:
    design = _load_design()
    light = design.design_light()
    regular = design.design_controls()
    bold = design.design_bold()
    assert light.context.stem < regular.context.stem < bold.context.stem
    assert regular.context.style.serif == "slab"


def test_slab_serif_build_script(tmp_path: Path) -> None:
    proc = subprocess.run(
        [sys.executable, "build_family.py", "--out", str(tmp_path)],
        cwd=EXAMPLE,
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr or proc.stdout
    assert "sentence gate ok" in proc.stdout
    assert len(list(tmp_path.glob("**/*.otf"))) == 3
    assert (tmp_path / "proof.png").is_file()
    assert (tmp_path / "proof_brief.png").is_file()
    assert (tmp_path / "review" / "review.json").is_file()
