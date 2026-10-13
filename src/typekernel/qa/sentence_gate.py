"""Agent-facing sentence quality gate (Controls pipeline, not legacy latin)."""

from __future__ import annotations

from dataclasses import dataclass

from typekernel.optics.glyph_polish import GlyphPolishOptions, polish_glyph_map
from typekernel.optics.space import space_font
from typekernel.parts.family import Controls
from typekernel.parts.metrics import (
    auto_class_kern,
    auto_side_kern_classes,
    rhythm_from_control_glyphs,
)
from typekernel.qa.score import WordReport, word_report

AGENT_SENTENCE = "Ideas ship farther. Build a brighter tomorrow."

__all__ = [
    "AGENT_SENTENCE",
    "SentenceGateLimits",
    "controls_sentence_report",
    "check_sentence_gate",
]


@dataclass(frozen=True, slots=True)
class SentenceGateLimits:
    """Regression thresholds for ``code_clear`` on :class:`Controls` (tighten over time)."""

    max_optical_gap_ratio: float = 1.45
    max_stem_cv: float = 0.15
    max_non_terminal_g1: int = 120


def _letters(text: str) -> str:
    return "".join(dict.fromkeys(ch for ch in text if ch.isalpha()))


def controls_sentence_report(
    controls: Controls,
    text: str = AGENT_SENTENCE,
) -> WordReport:
    """Score ``text`` after optical spacing on a Controls draw."""
    letters = _letters(text)
    ctx = controls.context
    charset = "".join(dict.fromkeys(letters + "no"))
    drawn = polish_glyph_map(
        controls.build_all(charset),
        GlyphPolishOptions(joins_policy="tangent_fix"),
    )
    rhythm = rhythm_from_control_glyphs(drawn["n"], drawn["o"])
    spaced = space_font(drawn, ctx, rhythm=rhythm)
    classes = auto_side_kern_classes(spaced, ctx)
    kern = auto_class_kern(spaced, classes, target=rhythm)
    names = [ch for ch in text if ch.isalpha()]
    glyphs = [spaced[ch] for ch in names]
    return word_report(glyphs, names, kerning=kern, target_gap=rhythm.target_gap)


def check_sentence_gate(
    controls: Controls,
    *,
    text: str = AGENT_SENTENCE,
    limits: SentenceGateLimits | None = None,
) -> tuple[WordReport, tuple[str, ...]]:
    """Return ``(report, failures)``; empty failures means pass."""
    lim = limits or SentenceGateLimits()
    report = controls_sentence_report(controls, text)
    failures: list[str] = []
    if report.optical_gap_ratio > lim.max_optical_gap_ratio:
        failures.append(
            f"optical_gap_ratio {report.optical_gap_ratio:.3f} > {lim.max_optical_gap_ratio}"
        )
    if report.stem_cv > lim.max_stem_cv:
        failures.append(f"stem_cv {report.stem_cv:.3f} > {lim.max_stem_cv}")
    nont = report.g1_join_error_count - report.terminal_count
    if nont > lim.max_non_terminal_g1:
        failures.append(f"non-terminal G1 errors: {nont} > {lim.max_non_terminal_g1}")
    return report, tuple(failures)
