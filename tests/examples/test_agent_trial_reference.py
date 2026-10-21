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
    validate_trial_snapshot,
)

ROOT = Path(__file__).resolve().parents[2]
TRIAL = ROOT / "examples" / "_legacy" / "agent_trial"
_METRICS_FIXTURE = (
    Path(__file__).resolve().parents[1] / "fixtures" / "reference_trial_metrics.json"
)

_REFERENCE_TRIALS = (
    ("brief-1", TRIAL / "design_warm_humanist.py"),
    ("brief-2", TRIAL / "design_editorial_geometric.py"),
    ("brief-3", TRIAL / "design_coding_clear.py"),
)

_METRICS_DESIGNS: dict[str, tuple[str, Path]] = {
    "brief-1": ("brief-1", TRIAL / "design_warm_humanist.py"),
    "brief-2": ("brief-2", TRIAL / "design_editorial_geometric.py"),
    "brief-2-slab": ("brief-2", TRIAL / "design_editorial_slab.py"),
    "brief-2-bracketed": ("brief-2", TRIAL / "design_editorial_bracketed.py"),
    "brief-3": ("brief-3", TRIAL / "design_coding_clear.py"),
}


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
    assert not snap.cheating_flags
    assert snap.program_pass_ok
    assert not validate_trial_snapshot(snap)


def test_reference_metrics_match_committed_fixture() -> None:
    """TK-502: documented voice_distance / gate metrics stay aligned with design_*.py."""
    expected = json.loads(_METRICS_FIXTURE.read_text(encoding="utf-8"))
    assert set(expected) == set(_METRICS_DESIGNS)
    for fixture_id, (brief_id, design_path) in _METRICS_DESIGNS.items():
        brief = next(b for b in FIXED_TRIAL_BRIEFS if b.id == brief_id)
        snap = snapshot_trial(_load_controls(design_path), brief=brief, round=1)
        row = expected[fixture_id]
        assert snap.family_gate_ok == row["family_gate_ok"]
        assert snap.l3_voice_ok == row["l3_voice_ok"]
        assert snap.weight_ladder_r8_failures == row["weight_ladder_r8_failures"]
        assert snap.lint_error_count == row["lint_error_count"]
        assert snap.identity_error_count == row["identity_error_count"]
        assert abs(snap.voice_distance - row["voice_distance"]) < 1e-5
        assert abs(snap.topology_fraction - row["topology_fraction"]) < 1e-5
        assert list(snap.cheating_flags) == row["cheating_flags"]
        assert snap.program_pass_ok == row["program_pass_ok"]
        if row["l3_voice_ok"]:
            from typekernel.qa.originality import L3_MIN_TOPOLOGY_FRACTION

            assert snap.topology_fraction >= L3_MIN_TOPOLOGY_FRACTION
        assert not validate_trial_snapshot(snap)


def test_reference_warm_humanist_passes_gate_and_r8() -> None:
    _assert_reference_trial("brief-1", _REFERENCE_TRIALS[0][1])


def test_reference_editorial_geometric_passes_l3() -> None:
    _assert_reference_trial("brief-2", _REFERENCE_TRIALS[1][1])


def test_reference_editorial_slab_passes_l3() -> None:
    _assert_reference_trial("brief-2", TRIAL / "design_editorial_slab.py")


def test_reference_editorial_bracketed_passes_l3() -> None:
    _assert_reference_trial("brief-2", TRIAL / "design_editorial_bracketed.py")


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
    for folder in (
        "brief-1",
        "brief-2",
        "brief-2-slab",
        "brief-2-bracketed",
        "brief-3",
    ):
        data = json.loads(
            (tmp_path / folder / "snapshot.json").read_text(encoding="utf-8")
        )
        assert data["l3_voice_ok"] is True
        assert data["program_pass_ok"] is True
    validate = subprocess.run(
        [
            sys.executable,
            "validate_snapshot.py",
            *[str(tmp_path / folder) for folder in (
                "brief-1",
                "brief-2",
                "brief-2-slab",
                "brief-2-bracketed",
                "brief-3",
            )],
        ],
        cwd=TRIAL,
        capture_output=True,
        text=True,
        check=False,
        env={**os.environ, "PYTHONPATH": str(ROOT / "src")},
    )
    assert validate.returncode == 0, validate.stderr or validate.stdout


def test_snapshot_design_stem_tweak_exit_code_7(tmp_path: Path) -> None:
    design = tmp_path / "stem_tweak.py"
    design.write_text(
        "from typekernel.parts import Controls, DesignContext\n\n"
        "def controls() -> Controls:\n"
        "    ctx = DesignContext.humanist_sans()\n"
        "    return Controls.from_context(ctx.tuned(stem=ctx.stem * 1.05))\n",
        encoding="utf-8",
    )
    proc = subprocess.run(
        [
            sys.executable,
            "snapshot_design.py",
            "--brief",
            "brief-1",
            "--design",
            str(design),
            "--out",
            str(tmp_path / "out"),
        ],
        cwd=TRIAL,
        capture_output=True,
        text=True,
        check=False,
        env={**os.environ, "PYTHONPATH": str(ROOT / "src")},
    )
    assert proc.returncode == 7, proc.stderr or proc.stdout
    data = json.loads((tmp_path / "out" / "snapshot.json").read_text(encoding="utf-8"))
    assert data["l3_voice_ok"] is False
    assert data["cheating_flags"] == ["stem_only_or_scale_voice"]


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
