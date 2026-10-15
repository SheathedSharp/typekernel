"""TK-502 reference design modules (not preset-only)."""

from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

from typekernel.parts import Controls
from typekernel.qa.trial_protocol import (
    FIXED_TRIAL_BRIEFS,
    L3_VOICE_DISTANCE_THRESHOLD,
    snapshot_trial,
)

ROOT = Path(__file__).resolve().parents[2]
TRIAL = ROOT / "examples" / "agent_trial"

_REFERENCE_TRIALS = (
    ("brief-1", TRIAL / "design_warm_humanist.py"),
    ("brief-2", TRIAL / "design_editorial_geometric.py"),
    ("brief-3", TRIAL / "design_coding_clear.py"),
)


def _load_controls(path: Path) -> Controls:
    spec = importlib.util.spec_from_file_location(path.stem, path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.controls()


def _assert_reference_trial(brief_id: str, design_path: Path) -> None:
    brief = next(b for b in FIXED_TRIAL_BRIEFS if b.id == brief_id)
    snap = snapshot_trial(
        _load_controls(design_path),
        brief=brief,
        round=1,
        apis_used=("Style", "terminal_style", "tuned_glyph"),
    )
    assert snap.family_gate_ok, snap.family_gate_failures
    assert snap.metrics_ok
    assert snap.weight_ladder_r8_failures == 0
    assert snap.l3_voice_ok
    assert snap.voice_distance >= L3_VOICE_DISTANCE_THRESHOLD
    assert snap.glyph_spec_chars


def test_reference_warm_humanist_passes_gate_and_r8() -> None:
    _assert_reference_trial("brief-1", _REFERENCE_TRIALS[0][1])


def test_reference_editorial_geometric_passes_l3() -> None:
    _assert_reference_trial("brief-2", _REFERENCE_TRIALS[1][1])


def test_reference_coding_clear_passes_l3() -> None:
    _assert_reference_trial("brief-3", _REFERENCE_TRIALS[2][1])


def test_snapshot_reference_trials_script(tmp_path: Path) -> None:
    proc = subprocess.run(
        [sys.executable, "snapshot_reference_trials.py", "--out", str(tmp_path)],
        cwd=TRIAL,
        capture_output=True,
        text=True,
        check=False,
        env={**os.environ, "PYTHONPATH": str(ROOT / "src")},
    )
    assert proc.returncode == 0, proc.stderr or proc.stdout
    for brief_id, _ in _REFERENCE_TRIALS:
        data = json.loads(
            (tmp_path / brief_id / "snapshot.json").read_text(encoding="utf-8")
        )
        assert data["l3_voice_ok"] is True


def test_snapshot_design_script(tmp_path: Path) -> None:
    proc = subprocess.run(
        [
            sys.executable,
            "snapshot_design.py",
            "--brief",
            "brief-1",
            "--design",
            str(_REFERENCE_TRIALS[0][1]),
            "--out",
            str(tmp_path),
        ],
        cwd=TRIAL,
        capture_output=True,
        text=True,
        check=False,
        env={**os.environ, "PYTHONPATH": str(ROOT / "src")},
    )
    assert proc.returncode == 0, proc.stderr or proc.stdout
    data = json.loads((tmp_path / "snapshot.json").read_text(encoding="utf-8"))
    assert data["brief_id"] == "brief-1"
    assert data["l3_voice_ok"] is True
    assert data["voice_distance"] >= L3_VOICE_DISTANCE_THRESHOLD
    assert "tuned_glyph" in data["apis_used"]
