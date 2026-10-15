"""TK-307 originality / voice distance metrics."""

from __future__ import annotations

import itertools

import pytest

from typekernel.parts import Controls, DesignContext
from typekernel.parts.style import Style
from typekernel.qa.originality import (
    BUILTIN_PRESET_FACTORIES,
    L3_MIN_TOPOLOGY_FRACTION,
    L3_VOICE_DISTANCE_THRESHOLD,
    l3_voice_criteria_met,
    nearest_voice_distance,
    originality_report,
    topology_fraction_vs_nearest_presets,
    topology_signature,
    voice_distance,
)

_PROBE_CHARSET = "noace"


def test_l3_threshold_frozen() -> None:
    assert L3_VOICE_DISTANCE_THRESHOLD == 0.35
    assert L3_MIN_TOPOLOGY_FRACTION == 0.05


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


@pytest.mark.parametrize(
    "factory",
    (DesignContext.slab_serif, DesignContext.bracketed_serif),
)
def test_l3_voice_criteria_met_for_serif_presets(factory) -> None:
    controls = Controls.from_context(factory())
    assert l3_voice_criteria_met(controls)


def test_l3_voice_criteria_not_met_for_unchanged_sans_preset() -> None:
    controls = Controls.from_context(DesignContext.humanist_sans())
    assert nearest_voice_distance(controls) < L3_VOICE_DISTANCE_THRESHOLD
    assert not l3_voice_criteria_met(controls)


def test_l3_voice_criteria_met_when_style_adds_slab_serif() -> None:
    """L3 must come from documented ``Style`` DNA, not an unchanged preset clone."""
    controls = Controls.from_context(
        DesignContext.humanist_sans(),
        style=Style(serif="slab"),
    )
    assert nearest_voice_distance(controls) >= L3_VOICE_DISTANCE_THRESHOLD
    assert l3_voice_criteria_met(controls)


def test_tuned_glyph_raises_nearest_distance() -> None:
    base = Controls.from_context(DesignContext.humanist_sans())
    tuned = base.tuned_glyph("f", arm=0.55).tuned_glyph("t", arm=0.45)
    assert nearest_voice_distance(tuned) > nearest_voice_distance(base)


def test_l3_rejects_context_only_stem_tweak() -> None:
    """TK-307: pure ``DesignContext`` scaling must not satisfy L3."""
    ctx = DesignContext.humanist_sans()
    tweaked = Controls.from_context(ctx.tuned(stem=ctx.stem * 1.05))
    assert nearest_voice_distance(tweaked) >= L3_VOICE_DISTANCE_THRESHOLD
    assert topology_fraction_vs_nearest_presets(tweaked) == 0.0
    assert not l3_voice_criteria_met(tweaked)


def test_slab_serif_preset_has_nearest_builtin_neighbor() -> None:
    controls = Controls.from_context(DesignContext.slab_serif())
    report = originality_report(controls)
    assert report.nearest_preset
    assert report.nearest_distance == 1.0


@pytest.mark.parametrize("preset_name", tuple(BUILTIN_PRESET_FACTORIES))
@pytest.mark.parametrize(
    "serif_factory",
    (DesignContext.slab_serif, DesignContext.bracketed_serif),
)
def test_tk307_serif_voices_far_from_every_builtin_preset(
    preset_name: str,
    serif_factory,
) -> None:
    """TK-307: TK-306 voices must diverge from all seven sans presets."""
    voice = Controls.from_context(serif_factory())
    ref = Controls.from_context(BUILTIN_PRESET_FACTORIES[preset_name]())
    dist = voice_distance(voice, ref)
    assert dist.combined >= L3_VOICE_DISTANCE_THRESHOLD
    assert dist.topology_fraction >= L3_MIN_TOPOLOGY_FRACTION


def test_topology_signature_differs_o_and_e() -> None:
    o = Controls.from_context(DesignContext.geometric_sans()).build_all("o")["o"]
    e = Controls.from_context(DesignContext.geometric_sans()).build_all("e")["e"]
    assert topology_signature(o) != topology_signature(e)
