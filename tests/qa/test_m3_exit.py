"""M3 exit: multiple distinct L3-capable voices (DEVELOPMENT_PLAN stage table)."""

from __future__ import annotations

import importlib.util
from pathlib import Path

from typekernel.parts import Controls, DesignContext
from typekernel.qa.originality import l3_voice_criteria_met, voice_distance

_ROOT = Path(__file__).resolve().parents[2]
_WARM_HUMANIST = _ROOT / "examples" / "agent_trial" / "design_warm_humanist.py"


def _load_controls(path: Path) -> Controls:
    spec = importlib.util.spec_from_file_location(path.stem, path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    sheet: Controls = mod.controls()
    return sheet


def test_m3_three_l3_voices_slab_bracketed_and_reference_sans() -> None:
    """Slab + bracketed presets and brief-1 reference edit all meet L3 program criteria."""
    slab = Controls.from_context(DesignContext.slab_serif())
    bracket = Controls.from_context(DesignContext.bracketed_serif())
    warm = _load_controls(_WARM_HUMANIST)
    for sheet in (slab, bracket, warm):
        assert l3_voice_criteria_met(sheet)


def test_m3_serif_pair_differs_from_warm_humanist_reference() -> None:
    """Three voices are not mutually identical on the shared charset."""
    slab = Controls.from_context(DesignContext.slab_serif())
    bracket = Controls.from_context(DesignContext.bracketed_serif())
    warm = _load_controls(_WARM_HUMANIST)
    assert voice_distance(slab, bracket).combined > 0.05
    assert voice_distance(slab, warm).combined > 0.05
    assert voice_distance(bracket, warm).combined > 0.05
