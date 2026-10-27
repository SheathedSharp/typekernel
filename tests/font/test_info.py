"""FontInfo.from_system (post-parts)."""

from __future__ import annotations

from typekernel.font.info import FontInfo, alignment_zones_from_system
from typekernel.system import Overshoot, System, Zones


def _system() -> System:
    return System(
        upm=1000,
        zones=Zones(base=0, x=520, cap=700, asc=740, desc=-200),
        overshoot=Overshoot(round=12, pointed=10),
        stem={"lc": 84, "uc": 92},
    )


def test_from_system_copies_zones() -> None:
    s = _system()
    info = FontInfo.from_system(s, "My Sans", "Bold", weight_class=700)
    assert info.family_name == "My Sans"
    assert info.style_name == "Bold"
    assert info.weight_class == 700
    assert info.x_height == s.zones.x
    assert info.cap_height == s.zones.cap
    assert info.ascender == s.zones.asc
    assert info.descender == s.zones.desc


def test_alignment_zones_from_system() -> None:
    blues, others = alignment_zones_from_system(_system())
    assert blues
