"""Generate kerning suggestions without applying them (P4-4 / target §7.2 E)."""

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


# Letter-agnostic seeds come from project kerning + proofs; this helper only
# expands a small control set when the project has none.
_DEFAULT_SEEDS: tuple[tuple[str, str], ...] = (
    ("A", "V"),
    ("A", "W"),
    ("A", "Y"),
    ("V", "A"),
    ("W", "A"),
    ("Y", "A"),
    ("T", "a"),
    ("T", "o"),
    ("T", "e"),
    ("T", "y"),
    ("F", "a"),
    ("F", "o"),
    ("F", "comma"),
    ("F", "period"),
    ("P", "a"),
    ("P", "o"),
    ("P", "period"),
    ("P", "comma"),
    ("L", "T"),
    ("L", "V"),
    ("L", "Y"),
    ("Y", "o"),
    ("Y", "a"),
    ("V", "o"),
    ("V", "a"),
    ("r", "a"),
    ("r", "o"),
    ("f", "a"),
    ("f", "o"),
    ("f", "period"),
    ("f", "comma"),
)


def default_seed_pairs() -> tuple[tuple[str, str], ...]:
    return _DEFAULT_SEEDS


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
    for a, b in _DEFAULT_SEEDS:
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
