"""Latin Sans family declaration — roman + true italic partner.

The italic partner is ``latin_sans_italic`` (matched proportions), not
humanist-italic. Linking uses :mod:`typekernel.axes.family`.
"""

from __future__ import annotations

from pathlib import Path

from typekernel.axes import FamilyMember, FamilySpec

__all__ = ["FAMILY", "ITALIC_ROOT", "ROMAN_ROOT", "link_built_pair"]

_STARTERS = Path(__file__).resolve().parents[1]
ROMAN_ROOT = _STARTERS / "latin_sans"
ITALIC_ROOT = _STARTERS / "latin_sans_italic"

FAMILY = FamilySpec(
    name="Latin Sans",
    members=(
        FamilyMember("Regular", italic=False, weight_class=400),
        FamilyMember("Italic", italic=True, weight_class=400),
    ),
)


def link_built_pair(roman_binary: str | Path, italic_binary: str | Path) -> list[Path]:
    """Apply shared typographic names + STAT ital to a built roman/italic pair."""
    from typekernel.axes.family import link_family

    return link_family(
        (
            (FAMILY.members[0], roman_binary),
            (FAMILY.members[1], italic_binary),
        ),
        FAMILY,
    )
