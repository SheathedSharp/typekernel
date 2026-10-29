"""Apply Metrics + Kerning onto a Font."""

from __future__ import annotations

from dataclasses import replace

from typekernel.font.font import Font
from typekernel.font.glyph import glyph_name_for_char
from typekernel.font.kerning import ClassKernPair, ClassKernTable, KernPair
from typekernel.metrics import Kerning, Metrics
from typekernel.metrics.packing import pack
from typekernel.metrics.resolving import resolve, resolve_side
from typekernel.system import System

__all__ = ["apply_kerning", "apply_metrics", "space_advance"]

# Control glyph for the legacy space formula (avoid AGL string literals).
_SPACE_CONTROL = chr(0x6E)  # Latin small letter n
_SPACE = glyph_name_for_char(" ")


def space_advance(
    metrics: Metrics,
    system: System,
    resolved: dict[str, tuple[float, float]],
) -> float | None:
    """Resolve the space glyph advance from Metrics.space / legacy tokens."""
    try:
        return resolve_side(metrics.space, system, resolved)
    except KeyError:
        pass
    # Legacy formula used by current starters when space_advance token is absent.
    tokens = system.tokens
    if "space_advance" in tokens:
        return float(tokens["space_advance"])
    if _SPACE_CONTROL in resolved:
        n_lsb, _ = resolved[_SPACE_CONTROL]
        stem_mul = float(tokens.get("space_stem_mul", 2.5))
        lsb_mul = float(tokens.get("space_lsb_mul", 0.5))
        return float(system.stem["lc"]) * stem_mul + n_lsb * lsb_mul
    return None


def apply_metrics(
    font: Font,
    metrics: Metrics,
    system: System,
) -> dict[str, tuple[float, float]]:
    """Pack sidebearings from metrics keys onto ``font``; set space width."""
    glyphs = {g.name: g for g in font}
    resolved = resolve(metrics, system, glyphs)
    policy = metrics.pack
    for name, (lsb, rsb) in resolved.items():
        if name not in font:
            continue
        font.add_glyph(
            pack(
                font[name],
                lsb,
                rsb,
                system,
                policy=policy,
                italic_pack_ys=metrics.italic_pack_ys,
            ),
            replace=True,
        )

    if _SPACE in font:
        adv = space_advance(metrics, system, resolved)
        if adv is not None:
            font.add_glyph(replace(font[_SPACE], advance=adv), replace=True)
    return resolved


def apply_kerning(font: Font, kerning: Kerning, *, strict: bool = False) -> None:
    """Write pair / class kerning onto ``font``."""
    pair_rows: list[KernPair] = []
    class_rows: list[ClassKernPair] = []
    for item in kerning.pairs:
        if isinstance(item, ClassKernPair):
            class_rows.append(item)
        else:
            pair_rows.append(item)
    pair_rows.extend(kerning.exceptions)

    if pair_rows:
        from typekernel.font.kerning import KernTable

        font.add_kern_table(KernTable(tuple(pair_rows)), strict=strict)
    if kerning.classes or class_rows:
        font.add_class_kern_table(
            ClassKernTable(classes=tuple(kerning.classes), pairs=tuple(class_rows)),
            strict=strict,
        )
