"""Agent-facing sentence quality gate (FormSources pipeline, not legacy latin).

Pass/fail always scores :data:`AGENT_SENTENCE`. A brief sentence is a second
specimen, not a way to pass. When ``baseline`` is set, the trial must not be
worse than that unmodified preset on optical gap ratio or non-terminal G1.
"""

from __future__ import annotations

from dataclasses import dataclass

from typekernel.optics.glyph_polish import GlyphPolishOptions, polish_glyph_map
from typekernel.optics.space import pair_gap_optical, space_font
from typekernel.parts.compose import ComposedGlyph
from typekernel.parts.family import FormSources
from typekernel.parts.metrics import (
    ClassKernTable,
    RhythmSpec,
    auto_class_kern,
    auto_side_kern_classes,
    rhythm_from_control_glyphs,
)
from typekernel.qa.score import WordReport, word_report

AGENT_SENTENCE = "Ideas ship farther. Build a brighter tomorrow."

# Fixed pair/word list. Collision means silhouette overlap, not "uneven colour".
AGENT_PAIRS = ("Ta", "To", "fi", "fl", "rn", "011")

# Float slack so an identical redraw is not a regression.
RELATIVE_RATIO_SLACK = 1e-3

__all__ = [
    "AGENT_PAIRS",
    "AGENT_SENTENCE",
    "RELATIVE_RATIO_SLACK",
    "PairGap",
    "SentenceGateLimits",
    "check_sentence_gate",
    "collect_gate_failures",
    "controls_pair_gaps",
    "controls_sentence_report",
    "non_terminal_g1",
]


@dataclass(frozen=True, slots=True)
class SentenceGateLimits:
    """Absolute regression ceilings (tighten over time). Not a beauty score."""

    max_optical_gap_ratio: float = 1.45
    max_stem_cv: float = 0.15
    max_non_terminal_g1: int = 120


@dataclass(frozen=True, slots=True)
class PairGap:
    """Optical gaps inside one fixed pair or word, after class kern."""

    text: str
    optical_gaps: tuple[float, ...]
    min_gap: float


def non_terminal_g1(report: WordReport) -> int:
    """G1 join errors that are not open terminals."""
    return report.g1_join_error_count - report.terminal_count


def _letters(text: str) -> str:
    return "".join(dict.fromkeys(ch for ch in text if ch.isalpha()))


def _spaced(
    controls: FormSources, charset: str
) -> tuple[dict[str, ComposedGlyph], ClassKernTable, RhythmSpec]:
    ctx = controls.context
    drawn_chars = "".join(dict.fromkeys(charset + "no"))
    drawn = polish_glyph_map(
        controls.derive(drawn_chars),
        GlyphPolishOptions(joins_policy="tangent_fix"),
    )
    rhythm = rhythm_from_control_glyphs(drawn["n"], drawn["o"])
    spaced = space_font(drawn, ctx, rhythm=rhythm)
    classes = auto_side_kern_classes(spaced, ctx)
    kern = auto_class_kern(spaced, classes, target=rhythm)
    return spaced, kern, rhythm


def controls_sentence_report(
    controls: FormSources,
    text: str = AGENT_SENTENCE,
) -> WordReport:
    """Score ``text`` after optical spacing on a FormSources draw."""
    letters = _letters(text)
    spaced, kern, rhythm = _spaced(controls, letters)
    names = [ch for ch in text if ch.isalpha()]
    glyphs = [spaced[ch] for ch in names]
    return word_report(glyphs, names, kerning=kern, target_gap=rhythm.target_gap)


def controls_pair_gaps(
    controls: FormSources,
    pairs: tuple[str, ...] = AGENT_PAIRS,
) -> tuple[PairGap, ...]:
    """Score each fixed pair/word. ``min_gap <= 0`` is a silhouette collision."""
    charset = "".join(dict.fromkeys("".join(pairs)))
    spaced, kern, _rhythm = _spaced(controls, charset)
    out: list[PairGap] = []
    for text in pairs:
        names = list(text)
        glyphs = [spaced[ch] for ch in names]
        gaps: list[float] = []
        for i in range(len(glyphs) - 1):
            kern_value = kern.lookup(names[i], names[i + 1])
            gaps.append(pair_gap_optical(glyphs[i], glyphs[i + 1], kern=kern_value))
        out.append(
            PairGap(
                text=text,
                optical_gaps=tuple(gaps),
                min_gap=min(gaps) if gaps else 0.0,
            )
        )
    return tuple(out)


def collect_gate_failures(
    report: WordReport,
    *,
    text: str = AGENT_SENTENCE,
    limits: SentenceGateLimits | None = None,
    baseline_report: WordReport | None = None,
    pairs: tuple[PairGap, ...] = (),
) -> tuple[str, ...]:
    """Turn a scored sentence (and optional pairs / preset) into failure strings.

    ``text`` is not scored here. Pass/fail text is always :data:`AGENT_SENTENCE`;
    any other string is itself a failure.
    """
    lim = limits or SentenceGateLimits()
    failures: list[str] = []
    if text != AGENT_SENTENCE:
        failures.append(
            "proof text is locked to AGENT_SENTENCE "
            f"(got {text!r}); brief sentences are a second specimen, not pass/fail"
        )
    if report.optical_gap_ratio > lim.max_optical_gap_ratio:
        failures.append(
            f"optical_gap_ratio {report.optical_gap_ratio:.3f} > {lim.max_optical_gap_ratio}"
        )
    if report.stem_cv > lim.max_stem_cv:
        failures.append(f"stem_cv {report.stem_cv:.3f} > {lim.max_stem_cv}")
    nont = non_terminal_g1(report)
    if nont > lim.max_non_terminal_g1:
        failures.append(f"non-terminal G1 errors: {nont} > {lim.max_non_terminal_g1}")
    if baseline_report is not None:
        base_ratio = baseline_report.optical_gap_ratio
        if report.optical_gap_ratio > base_ratio + RELATIVE_RATIO_SLACK:
            failures.append(
                f"optical_gap_ratio {report.optical_gap_ratio:.3f} > "
                f"preset baseline {base_ratio:.3f}"
            )
        base_g1 = non_terminal_g1(baseline_report)
        if nont > base_g1:
            failures.append(f"non-terminal G1 {nont} > preset baseline {base_g1}")
    for pair in pairs:
        if pair.min_gap <= 0.0:
            failures.append(f"pair {pair.text!r} collides: min optical gap {pair.min_gap:.1f} <= 0")
    return tuple(failures)


def check_sentence_gate(
    controls: FormSources,
    *,
    text: str = AGENT_SENTENCE,
    limits: SentenceGateLimits | None = None,
    baseline: FormSources | None = None,
) -> tuple[WordReport, tuple[str, ...]]:
    """Return ``(report, failures)`` for :data:`AGENT_SENTENCE`.

    The report is always the locked sentence, even when ``text`` differs.
    ``baseline`` is the unmodified preset (``FormSources.from_context(preset())``);
    the trial must not worsen its optical gap ratio or non-terminal G1.
    """
    report = controls_sentence_report(controls, AGENT_SENTENCE)
    pairs = controls_pair_gaps(controls)
    baseline_report = (
        None if baseline is None else controls_sentence_report(baseline, AGENT_SENTENCE)
    )
    failures = collect_gate_failures(
        report,
        text=text,
        limits=limits,
        baseline_report=baseline_report,
        pairs=pairs,
    )
    return report, failures
