"""Family linking: shared typographic names + STAT ``ital`` (P4-6).

Roman and italic partners must share a typographic family name (name ID 16)
and expose a consistent STAT ``ital`` axis so OS / browsers treat them as one
family. True italic outlines arrive in P5; this module links any pair —
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


def _set_name(tt, name_id: int, string: str, *, platform_id: int = 3, plat_enc_id: int = 1, lang_id: int = 0x409) -> None:
    from fontTools.ttLib import TTFont  # noqa: F401 — typing aid
    name = tt["name"]
    name.setName(string, name_id, platform_id, plat_enc_id, lang_id)
    # Also Mac Roman for broader tooling.
    try:
        name.setName(string, name_id, 1, 0, 0)
    except Exception:
        pass


def apply_family_names(tt, family: FamilySpec, member: FamilyMember) -> None:
    """Write name IDs 1/2/4/6/16/17 for ``member`` under ``family.name``."""
    # RIBBI-compatible: Family (1) + Subfamily (2); Typographic (16/17) for larger sets.
    family_ribbi = family.name
    subfamily = "Italic" if member.italic and member.style_name in {"Italic", "Oblique"} else member.style_name
    if member.italic and "Italic" not in subfamily and "Oblique" not in subfamily:
        subfamily = f"{member.style_name} Italic"
    typo_family = family.name
    typo_subfamily = member.style_name if member.style_name not in {"Regular", "Italic"} else (
        "Italic" if member.italic else "Regular"
    )
    if member.italic and member.style_name in {"Italic", "Oblique"}:
        typo_subfamily = "Italic"

    full = f"{typo_family} {typo_subfamily}".strip()
    postscript = f"{typo_family}-{typo_subfamily}".replace(" ", "")

    _set_name(tt, 1, family_ribbi)
    _set_name(tt, 2, subfamily if member.style_name in {"Regular", "Italic", "Bold", "Bold Italic"} or member.italic else member.style_name)
    # Prefer classic RIBBI for Regular/Italic pair.
    if member.italic and member.weight_class == 400:
        _set_name(tt, 2, "Italic")
    elif not member.italic and member.weight_class == 400 and member.style_name in {"Regular", "Roman"}:
        _set_name(tt, 2, "Regular")
    _set_name(tt, 4, full)
    _set_name(tt, 6, postscript)
    _set_name(tt, 16, typo_family)
    _set_name(tt, 17, typo_subfamily)

    if "OS/2" in tt:
        os2 = tt["OS/2"]
        os2.usWeightClass = int(member.weight_class)
        # bit 0 = italic
        fs = int(getattr(os2, "fsSelection", 0) or 0)
        if member.italic:
            fs = (fs | 0x01) & ~0x40  # italic, clear regular
        else:
            fs = (fs | 0x40) & ~0x01  # regular, clear italic
        os2.fsSelection = fs
    if "head" in tt:
        head = tt["head"]
        mac = int(getattr(head, "macStyle", 0) or 0)
        if member.italic:
            mac |= 0x02
        else:
            mac &= ~0x02
        head.macStyle = mac
    if member.italic and "post" in tt:
        # Synthetic oblique fixture uses ~−12°; leave existing if set.
        if getattr(tt["post"], "italicAngle", 0) == 0:
            tt["post"].italicAngle = -12.0


def apply_family_stat(tt, family: FamilySpec, member: FamilyMember) -> None:
    """Install a minimal STAT with ``ital`` (and optional ``wght``) for linking."""
    from fontTools.otlLib.builder import buildStatTable

    axes = [
        dict(
            tag="ital",
            name="Italic",
            ordering=1,
            values=[
                dict(value=0, name="Roman", flags=2, linkedValue=1),  # ElidableAxisValueName
                dict(value=1, name="Italic"),
            ],
        )
    ]
    # If the face already exposes wght via fvar, mirror a weight axis into STAT.
    if "fvar" in tt:
        for ax in tt["fvar"].axes:
            if ax.axisTag == "wght":
                axes.insert(
                    0,
                    dict(
                        tag="wght",
                        name="Weight",
                        ordering=0,
                        values=[
                            dict(
                                value=float(member.weight_class),
                                name=member.style_name.replace(" Italic", "").replace(" Oblique", "")
                                or ("Regular" if not member.italic else "Regular"),
                            )
                        ],
                    ),
                )
                break
    else:
        # Static pair: still record weight for the member.
        axes.insert(
            0,
            dict(
                tag="wght",
                name="Weight",
                ordering=0,
                values=[
                    dict(
                        value=float(member.weight_class),
                        name="Regular" if member.weight_class == 400 else str(member.weight_class),
                        flags=2 if member.weight_class == 400 else 0,
                    )
                ],
            ),
        )

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
        v = name.getDebugName(nid)
        return v

    ital_values: list[float] = []
    if "STAT" in tt:
        stat = tt["STAT"].table
        for avs in getattr(stat, "AxisValueArray", None) and stat.AxisValueArray.AxisValue or []:
            # Format 1/2/3/4 — collect ital axis values when tag matches.
            pass
        axis_records = list(stat.DesignAxisRecord.Axis)
        tags = [a.AxisTag for a in axis_records]
        # Axis values
        if stat.AxisValueArray is not None:
            for av in stat.AxisValueArray.AxisValue:
                axis_tag = tags[av.AxisIndex] if hasattr(av, "AxisIndex") else None
                if axis_tag == "ital" and hasattr(av, "Value"):
                    ital_values.append(float(av.Value))
    else:
        tags = []

    os2 = tt["OS/2"] if "OS/2" in tt else None
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
