"""System / Zones / Overshoot (System)."""

from __future__ import annotations

import pytest

from typekernel.system import Overshoot, System, Zones


def _regular() -> System:
    return System(
        upm=1000,
        zones=Zones(base=0, x=520, cap=700, asc=740, desc=-210),
        overshoot=Overshoot(round=12, pointed=10),
        stem={"lc": 84, "lc_h": 70, "uc": 92},
        tokens={"shoulder_tension": 0.58},
    )


def test_system_fields_are_frozen_mappings() -> None:
    s = _regular()
    assert s.upm == 1000
    assert s.zones.x == 520
    assert s.overshoot.round == 12
    assert s.stem["lc"] == 84
    with pytest.raises(TypeError):
        s.stem["lc"] = 1  # type: ignore[index]
    with pytest.raises(TypeError):
        s.tokens["extra"] = 1  # type: ignore[index]


def test_tuned_replaces_fields_and_preserves_rest() -> None:
    s = _regular()
    t = s.tuned(stem={"lc": 100}, tokens={"n_width": 430})
    assert t.stem["lc"] == 100
    assert t.tokens["n_width"] == 430
    assert t.zones is s.zones
    assert t.overshoot is s.overshoot
    assert s.stem["lc"] == 84  # original untouched


def test_no_aperture_or_roundness_attributes() -> None:
    s = _regular()
    assert not hasattr(s, "aperture")
    assert not hasattr(s, "roundness")


def test_system_slant_defaults_upright() -> None:
    s = _regular()
    assert s.slant == 0.0
    assert not s.is_italic
    assert s.stem_direction_deg() == 90.0
    assert s.slant_dx(100.0) == 0.0
    assert s.map_xy(10.0, 100.0) == (10.0, 100.0)


def test_system_slant_helpers() -> None:
    s = _regular().tuned(slant=0.2)
    assert s.is_italic
    assert abs(s.slant_dx(100.0) - 20.0) < 1e-9
    assert s.map_xy(10.0, 100.0) == (30.0, 100.0)
    # atan2(1, 0.2) degrees
    import math

    assert abs(s.stem_direction_deg() - math.degrees(math.atan2(1.0, 0.2))) < 1e-9
