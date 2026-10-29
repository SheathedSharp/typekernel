"""Family linking: shared typographic names + STAT ``ital``.

Roman and italic partners must share a typographic family name (name ID 16)
and expose a consistent STAT ``ital`` axis so OS / browsers treat them as one
family. True italic outlines arrive as separate starters; this module links any pair —
including a synthetic oblique fixture — at the name / STAT layer.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path

__all__ = [
    "FamilyMember",
    "FamilySpec",
    "apply_family_names",
    "apply_family_stat",
    "link_family",
    "read_family_identity",
]


@dataclass(frozen=True, slots=True)
class FamilyMember:
    """One face in a linked family (roman or italic)."""

    style_name: str
    italic: bool = False
    weight_class: int = 400
    location: Mapping[str, float] | None = None


@dataclass(frozen=True, slots=True)
class FamilySpec:
    """Typographic family declaration used for name + STAT linking."""

    name: str
    members: Sequence[FamilyMember]


def _set_name(
    tt: object,
    name_id: int,
    string: str,
    *,
    platform_id: int = 3,
    plat_enc_id: int = 1,
    lang_id: int = 0x409,
) -> None:
    name = tt["name"]  # type: ignore[index]
    name.setName(string, name_id, platform_id, plat_enc_id, lang_id)
    # Mac Roman (platform 1) for broader tooling; skip if the string is not encodable.
    try:
        string.encode("mac_roman")
    except UnicodeEncodeError:
        return
    name.setName(string, name_id, 1, 0, 0)


def _ribbi_subfamily(member: FamilyMember) -> str:
    if member.italic and member.weight_class == 400:
        return "Italic"
    if not member.italic and member.weight_class == 400:
        return "Regular"
    if member.italic and member.weight_class == 700:
        return "Bold Italic"
    if not member.italic and member.weight_class == 700:
        return "Bold"
    return member.style_name


def _typo_subfamily(member: FamilyMember) -> str:
    if member.style_name in {"Regular", "Roman"} and not member.italic:
        return "Regular"
    if member.style_name in {"Italic", "Oblique"} or (
        member.italic and member.weight_class == 400 and member.style_name in {"Italic", "Oblique", "Regular"}
    ):
        return "Italic"
    if member.italic and "Italic" not in member.style_name:
        return f"{member.style_name} Italic"
    return member.style_name


def apply_family_names(tt: object, family: FamilySpec, member: FamilyMember) -> None:
    """Write name IDs 1/2/4/6/16/17 for ``member`` under ``family.name``."""
    subfamily = _ribbi_subfamily(member)
    typo_family = family.name
    typo_subfamily = _typo_subfamily(member)
    full = f"{typo_family} {typo_subfamily}".strip()
    postscript = f"{typo_family}-{typo_subfamily}".replace(" ", "")

    _set_name(tt, 1, family.name)
    _set_name(tt, 2, subfamily)
    _set_name(tt, 4, full)
    _set_name(tt, 6, postscript)
    _set_name(tt, 16, typo_family)
    _set_name(tt, 17, typo_subfamily)

    os2 = tt.get("OS/2")  # type: ignore[attr-defined]
    if os2 is not None:
        os2.usWeightClass = int(member.weight_class)
        fs = int(getattr(os2, "fsSelection", 0) or 0)
        if member.italic:
            fs = (fs | 0x01) & ~0x40
        else:
            fs = (fs | 0x40) & ~0x01
        os2.fsSelection = fs

    head = tt.get("head")  # type: ignore[attr-defined]
    if head is not None:
        mac = int(getattr(head, "macStyle", 0) or 0)
        head.macStyle = (mac | 0x02) if member.italic else (mac & ~0x02)

    post = tt.get("post")  # type: ignore[attr-defined]
    if member.italic and post is not None and getattr(post, "italicAngle", 0) == 0:
        post.italicAngle = -12.0


def apply_family_stat(tt: object, family: FamilySpec, member: FamilyMember) -> None:
    """Install a minimal STAT with ``ital`` (and ``wght``) for linking."""
    from fontTools.otlLib.builder import buildStatTable

    weight_name = (
        member.style_name.replace(" Italic", "").replace(" Oblique", "") or "Regular"
    )
    if weight_name in {"Italic", "Oblique"}:
        weight_name = "Regular"

    axes: list[dict] = [
        {
            "tag": "wght",
            "name": "Weight",
            "ordering": 0,
            "values": [
                {
                    "value": float(member.weight_class),
                    "name": weight_name,
                    "flags": 2 if member.weight_class == 400 else 0,
                }
            ],
        },
        {
            "tag": "ital",
            "name": "Italic",
            "ordering": 1,
            "values": [
                {"value": 0, "name": "Roman", "flags": 2, "linkedValue": 1},
                {"value": 1, "name": "Italic"},
            ],
        },
    ]
    locations = [
        {
            "name": member.style_name,
            "location": {
                "wght": float(member.weight_class),
                "ital": 1 if member.italic else 0,
            },
        }
    ]
    buildStatTable(tt, axes, locations=locations)


def link_family(
    paths: Mapping[FamilyMember, str | Path] | Sequence[tuple[FamilyMember, str | Path]],
    family: FamilySpec,
    *,
    overwrite: bool = True,
) -> list[Path]:
    """Apply names + STAT to each member binary; return written paths."""
    from fontTools.ttLib import TTFont

    items: Sequence[tuple[FamilyMember, str | Path]]
    if isinstance(paths, Mapping):
        items = list(paths.items())
    else:
        items = list(paths)

    written: list[Path] = []
    for member, path in items:
        src = Path(path)
        tt = TTFont(src)
        apply_family_names(tt, family, member)
        apply_family_stat(tt, family, member)
        dest = src if overwrite else src.with_name(src.stem + "-linked" + src.suffix)
        tt.save(dest)
        written.append(dest)
    return written


def read_family_identity(path: str | Path) -> dict[str, object]:
    """Read name / STAT / OS/2 fields used to verify family linking."""
    from fontTools.ttLib import TTFont

    tt = TTFont(Path(path))
    name = tt["name"]

    def get(nid: int) -> str | None:
        return name.getDebugName(nid)

    ital_values: list[float] = []
    tags: list[str] = []
    if "STAT" in tt:
        stat = tt["STAT"].table
        axis_records = list(stat.DesignAxisRecord.Axis)
        tags = [a.AxisTag for a in axis_records]
        if stat.AxisValueArray is not None:
            for av in stat.AxisValueArray.AxisValue:
                if hasattr(av, "AxisIndex"):
                    axis_tag = tags[av.AxisIndex]
                    if axis_tag == "ital" and hasattr(av, "Value"):
                        ital_values.append(float(av.Value))

    os2 = tt.get("OS/2")
    return {
        "family_name_id1": get(1),
        "subfamily_id2": get(2),
        "typo_family_id16": get(16),
        "typo_subfamily_id17": get(17),
        "full_name_id4": get(4),
        "stat_axes": tags,
        "stat_ital_values": ital_values,
        "fs_selection_italic": bool(os2 and (os2.fsSelection & 0x01)),
        "weight_class": int(os2.usWeightClass) if os2 else None,
    }
