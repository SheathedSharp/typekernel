"""TK-502 reference design module (not preset-only)."""

from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

from typekernel.parts import Controls
from typekernel.qa.trial_protocol import FIXED_TRIAL_BRIEFS, snapshot_trial

ROOT = Path(__file__).resolve().parents[2]
TRIAL = ROOT / "examples" / "agent_trial"
DESIGN = TRIAL / "design_warm_humanist.py"

# Below L3 (0.35) but well above unchanged preset (~0).
_MIN_REFERENCE_VOICE_DISTANCE = 0.2


def _load_controls() -> Controls:
    spec = importlib.util.spec_from_file_location("design_warm_humanist", DESIGN)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.controls()


def test_reference_warm_humanist_passes_gate_and_r8() -> None:
    brief = next(b for b in FIXED_TRIAL_BRIEFS if b.id == "brief-1")
    snap = snapshot_trial(
        _load_controls(),
        brief=brief,
        round=1,
        apis_used=("Style", "terminal_style", "tuned_glyph"),
    )
    assert snap.family_gate_ok, snap.family_gate_failures
    assert snap.metrics_ok
    assert snap.weight_ladder_r8_failures == 0
    assert snap.voice_distance >= _MIN_REFERENCE_VOICE_DISTANCE
    assert "f" in snap.glyph_spec_chars


def test_snapshot_design_script(tmp_path: Path) -> None:
    proc = subprocess.run(
        [
            sys.executable,
            "snapshot_design.py",
            "--brief",
            "brief-1",
            "--design",
            str(DESIGN),
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
    assert data["voice_distance"] >= _MIN_REFERENCE_VOICE_DISTANCE
    assert "tuned_glyph" in data["apis_used"]
