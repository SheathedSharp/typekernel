"""L2 family template: three masters, locked gate, shared compile path."""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest

from typekernel.parts import Controls, DesignContext

pytest.importorskip("ufoLib2")
pytest.importorskip("PIL")

ROOT = Path(__file__).resolve().parents[2]
FAMILY = ROOT / "examples" / "agent_family"


def _load_design():
    spec = importlib.util.spec_from_file_location(
        "agent_family_design",
        FAMILY / "design.py",
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_family_masters_are_separate_sheets() -> None:
    design = _load_design()
    regular = design.design_controls()
    light = design.design_light()
    bold = design.design_bold()
    assert light.context.stem < regular.context.stem < bold.context.stem
    plain_bold = Controls.from_context(
        DesignContext.humanist_sans().tuned(stem=bold.context.stem, sidebearing_ratio=0.11)
    )
    assert bold.n.counter >= plain_bold.n.counter
    assert {"f", "t"} <= set(regular.glyph_overrides)


def test_agent_family_build_script(tmp_path: Path) -> None:
    proc = subprocess.run(
        [sys.executable, "build_family.py", "--out", str(tmp_path)],
        cwd=FAMILY,
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr or proc.stdout
    assert "sentence gate ok" in proc.stdout
    otfs = list(tmp_path.glob("*.otf"))
    assert len(otfs) == 3
    assert (tmp_path / "proof.png").is_file()
    assert (tmp_path / "proof_brief.png").is_file()
    assert (tmp_path / "review" / "review.json").is_file()
