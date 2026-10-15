"""TK-306 slab serif example: gate, build, proof artifacts."""

from __future__ import annotations

import importlib.util
import os
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


def test_slab_voice_masters_interpolate_on_vf_ladder() -> None:
    from typekernel.font import Font, Master, check_masters
    from typekernel.parts import DesignContext

    design = _load_design()
    ctx = DesignContext.slab_serif()
    ladder = ((70.0, 300, False), (100.0, 400, False), (140.0, 600, False), (180.0, 700, True))
    fonts = []
    for stem, wght, relief in ladder:
        controls = design._voice(stem, relief=relief)
        font = Font.from_context(ctx, "Slab", f"W{wght}", weight_class=wght)
        font.add_chars(controls.build_all())
        fonts.append(font)
    masters = [Master({"wght": float(w)}, f) for (_, w, _), f in zip(ladder, fonts, strict=True)]
    assert check_masters(masters) == []


def test_slab_preset_stems_order_light_regular_bold() -> None:
    design = _load_design()
    light = design.design_light()
    regular = design.design_controls()
    bold = design.design_bold()
    assert light.context.stem < regular.context.stem < bold.context.stem
    assert regular.context.style.serif == "slab"


def test_slab_serif_build_vf_script(tmp_path: Path) -> None:
    proc = subprocess.run(
        [sys.executable, "build_vf.py", "--out", str(tmp_path)],
        cwd=EXAMPLE,
        capture_output=True,
        text=True,
        check=False,
        env={**os.environ, "PYTHONPATH": str(ROOT / "src")},
    )
    assert proc.returncode == 0, proc.stderr or proc.stdout
    assert (tmp_path / "TypekernelSlab-VF.ttf").is_file()
    assert (tmp_path / "proof_vf.png").is_file()


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
