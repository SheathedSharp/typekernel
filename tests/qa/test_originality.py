"""TK-307 originality / voice distance metrics."""

from __future__ import annotations

import itertools

import pytest

from typekernel.parts import Controls, DesignContext
from typekernel.qa.originality import (
    BUILTIN_PRESET_FACTORIES,
    L3_VOICE_DISTANCE_THRESHOLD,
    nearest_voice_distance,
    originality_report,
    topology_signature,
    voice_distance,
)

_PROBE_CHARSET = "noace"


def test_l3_threshold_frozen() -> None:
    assert L3_VOICE_DISTANCE_THRESHOLD == 0.35


@pytest.mark.parametrize("name", tuple(BUILTIN_PRESET_FACTORIES))
def test_preset_nearest_neighbor_is_self(name: str) -> None:
    controls = Controls.from_context(BUILTIN_PRESET_FACTORIES[name]())
    report = originality_report(controls, _PROBE_CHARSET)
    assert report.nearest_preset == name
    assert report.nearest_distance < 1e-9


def test_seven_builtin_presets() -> None:
    assert len(BUILTIN_PRESET_FACTORIES) == 7


def test_presets_share_topology_on_probe_charset() -> None:
    """Baseline: presets differ in shape knobs, not letter topology."""
    names = tuple(BUILTIN_PRESET_FACTORIES)
    sheets = {
        n: Controls.from_context(BUILTIN_PRESET_FACTORIES[n]()) for n in names
    }
    for a, b in itertools.combinations(names, 2):
        vd = voice_distance(sheets[a], sheets[b], _PROBE_CHARSET)
        assert vd.topology_fraction == 0.0
        assert vd.shape_fraction > 0.0


def test_slab_serif_meets_l3_voice_distance() -> None:
    controls = Controls.from_context(DesignContext.slab_serif())
    assert nearest_voice_distance(controls) >= L3_VOICE_DISTANCE_THRESHOLD


def test_bracketed_serif_meets_l3_voice_distance() -> None:
    controls = Controls.from_context(DesignContext.bracketed_serif())
    assert nearest_voice_distance(controls) >= L3_VOICE_DISTANCE_THRESHOLD


def test_tuned_glyph_raises_nearest_distance() -> None:
    base = Controls.from_context(DesignContext.humanist_sans())
    tuned = base.tuned_glyph("f", arm=0.55).tuned_glyph("t", arm=0.45)
    assert nearest_voice_distance(tuned) > nearest_voice_distance(base)


def test_topology_signature_differs_o_and_e() -> None:
    o = Controls.from_context(DesignContext.geometric_sans()).build_all("o")["o"]
    e = Controls.from_context(DesignContext.geometric_sans()).build_all("e")["e"]
    assert topology_signature(o) != topology_signature(e)
