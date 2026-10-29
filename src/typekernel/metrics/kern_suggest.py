"""Generate kerning suggestions without applying them (target §7.2 E)."""

from __future__ import annotations

import json
from collections.abc import Iterable, Sequence
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from typekernel.font.kerning import KernPair
from typekernel.optics.space import fit_kern_pair, pair_gap_bbox, pair_gap_optical

if TYPE_CHECKING:
    from typekernel.project.session import ProjectSession

__all__ = [
    "KernSuggestion",
    "default_seed_pairs",
    "suggest_kern_pairs",
    "write_suggestions",
]


@dataclass(frozen=True, slots=True)
class KernSuggestion:
    left: str
    right: str
    current: float
    suggested: float
    gap_bbox: float
    gap_optical: float
    reason: str


# Fallback control pairs as Unicode codepoints → AGL names via the public
# glyph-name API (no hard-coded letter / AGL string literals in the kernel).
_DEFAULT_SEED_CODEPOINTS: tuple[tuple[int, int], ...] = (
    (0x41, 0x56),  # A V
    (0x41, 0x57),  # A W
    (0x41, 0x59),  # A Y
    (0x56, 0x41),  # V A
    (0x57, 0x41),  # W A
    (0x59, 0x41),  # Y A
    (0x54, 0x61),  # T a
    (0x54, 0x6F),  # T o
    (0x54, 0x65),  # T e
    (0x54, 0x79),  # T y
    (0x46, 0x61),  # F a
    (0x46, 0x6F),  # F o
    (0x46, 0x2C),  # F comma
    (0x46, 0x2E),  # F period
    (0x50, 0x61),  # P a
    (0x50, 0x6F),  # P o
    (0x50, 0x2E),  # P period
    (0x50, 0x2C),  # P comma
    (0x4C, 0x54),  # L T
    (0x4C, 0x56),  # L V
    (0x4C, 0x59),  # L Y
    (0x59, 0x6F),  # Y o
    (0x59, 0x61),  # Y a
    (0x56, 0x6F),  # V o
    (0x56, 0x61),  # V a
    (0x72, 0x61),  # r a
    (0x72, 0x6F),  # r o
    (0x66, 0x61),  # f a
    (0x66, 0x6F),  # f o
    (0x66, 0x2E),  # f period
    (0x66, 0x2C),  # f comma
)


def default_seed_pairs() -> tuple[tuple[str, str], ...]:
    from typekernel.font.glyph import glyph_name_for_char

    return tuple(
        (glyph_name_for_char(chr(a)), glyph_name_for_char(chr(b)))
        for a, b in _DEFAULT_SEED_CODEPOINTS
    )


def _current_kern(session: ProjectSession, left: str, right: str) -> float:
    kerning = session.project.kerning
    if kerning is None:
        return 0.0
    for item in kerning.pairs:
        if isinstance(item, KernPair) and item.left == left and item.right == right:
            return float(item.value)
    for item in kerning.exceptions:
        if item.left == left and item.right == right:
            return float(item.value)
    return 0.0


def _seed_pairs(session: ProjectSession) -> list[tuple[str, str]]:
    specs = session.specs()
    seen: set[tuple[str, str]] = set()
    out: list[tuple[str, str]] = []

    def add(a: str, b: str) -> None:
        if a in specs and b in specs and (a, b) not in seen:
            seen.add((a, b))
            out.append((a, b))

    kerning = session.project.kerning
    if kerning is not None:
        for item in list(kerning.pairs) + list(kerning.exceptions):
            if isinstance(item, KernPair):
                add(item.left, item.right)
    for a, b in default_seed_pairs():
        add(a, b)
    return out


def suggest_kern_pairs(
    session: ProjectSession,
    *,
    master: str | None = None,
    target_gap: float = 24.0,
    pairs: Sequence[tuple[str, str]] | None = None,
    min_abs: float = 4.0,
) -> list[KernSuggestion]:
    """Propose kern values so optical gap ≈ ``target_gap`` (bbox gap ≥ 0).

    Suggestions are data only — callers write a file; nothing is auto-applied.
    """
    seeds = list(pairs) if pairs is not None else _seed_pairs(session)
    suggestions: list[KernSuggestion] = []
    for left_name, right_name in seeds:
        if left_name not in session.specs() or right_name not in session.specs():
            continue
        left = session.glyph(left_name, master=master)
        right = session.glyph(right_name, master=master)
        current = _current_kern(session, left_name, right_name)
        # Optical fit, then clamp so bbox gap stays non-negative.
        optical = fit_kern_pair(left, right, target_gap)
        bbox0 = pair_gap_bbox(left, right, kern=0.0)
        # kern >= -bbox0 keeps bbox gap >= 0
        floor = -bbox0
        clamped = optical < floor
        suggested = floor if clamped else optical
        # Round to whole design units
        suggested = float(round(suggested))
        # Drop tiny optional tweaks, but never drop a clamp that clears a collision.
        if not clamped and abs(suggested) < min_abs:
            suggested = 0.0
        gap_b = pair_gap_bbox(left, right, kern=suggested)
        gap_o = pair_gap_optical(left, right, kern=suggested)
        reason = "clamped to non-negative bbox gap" if clamped else "fit optical"
        if abs(suggested - current) < 0.5 and gap_b >= -0.5:
            continue  # already good
        suggestions.append(
            KernSuggestion(
                left=left_name,
                right=right_name,
                current=current,
                suggested=suggested,
                gap_bbox=float(gap_b),
                gap_optical=float(gap_o),
                reason=reason,
            )
        )
    return suggestions


def write_suggestions(
    suggestions: Iterable[KernSuggestion],
    path: str | Path,
) -> Path:
    """Write JSON suggestions (not applied to the project)."""
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "note": "Kerning suggestions — review before adopting into spacing.py. Not auto-applied.",
        "pairs": [asdict(s) for s in suggestions],
    }
    out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return out
