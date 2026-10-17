"""Designer-style review for a Controls sheet.

Numbers tell the agent what to change next: preset deltas, weak-glyph join
counts, and the worst fixed pairs. PNGs are previews; cubics stay the truth.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

from typekernel.geo.outline import Outline
from typekernel.optics.glyph_polish import GlyphPolishOptions, polish_glyph_map
from typekernel.parts.compose import ComposedGlyph
from typekernel.parts.family import Controls
from typekernel.qa.family_gate import collect_family_gate_failures
from typekernel.qa.score import WordReport, join_smoothness_glyph
from typekernel.qa.sentence_gate import (
    AGENT_PAIRS,
    AGENT_SENTENCE,
    RELATIVE_RATIO_SLACK,
    PairGap,
    collect_gate_failures,
    controls_pair_gaps,
    controls_sentence_report,
    non_terminal_g1,
)

# Letters agents must master by hand before calling a trial done.
WEAK_GLYPHS = ("f", "t", "j", "a", "s", "e")
# Control glyphs plus the letters a review should look at after the grid.
REVIEW_GLYPHS = ("n", "o", "H", "O", "a", "s", "e", "r", "t", "f", "I")
L0_MIN_WEAK_OVERRIDES = 2

__all__ = [
    "L0_MIN_WEAK_OVERRIDES",
    "REVIEW_GLYPHS",
    "WEAK_GLYPHS",
    "DesignReview",
    "GlyphScore",
    "MetricDelta",
    "design_review",
]


@dataclass(frozen=True, slots=True)
class MetricDelta:
    """Trial versus the unmodified preset. ``worse`` is the gate direction."""

    name: str
    trial: float
    baseline: float
    worse: bool


@dataclass(frozen=True, slots=True)
class GlyphScore:
    """One reviewed glyph after join polish."""

    char: str
    g1_errors: int
    overridden: bool


@dataclass(frozen=True, slots=True)
class DesignReview:
    """What to read before the next edit. Empty ``failures`` is not a family."""

    sentence: WordReport
    failures: tuple[str, ...]
    pairs: tuple[PairGap, ...]
    deltas: tuple[MetricDelta, ...]
    glyphs: tuple[GlyphScore, ...]
    l0_gaps: tuple[str, ...]
    charset_failures: tuple[str, ...] = ()
    sequence_failures: tuple[str, ...] = ()
    notes: tuple[str, ...] = ()

    @property
    def worst_pairs(self) -> tuple[PairGap, ...]:
        """Pairs sorted tightest optical gap first."""
        return tuple(sorted(self.pairs, key=lambda pair: pair.min_gap))

    def summary(self) -> str:
        """Short log for a build script."""
        lines: list[str] = []
        if self.failures or self.l0_gaps:
            lines.append("sentence gate FAIL")
        else:
            lines.append(
                "sentence gate ok · "
                f"optical ratio {self.sentence.optical_gap_ratio:.3f} · "
                f"G1(non-term) {non_terminal_g1(self.sentence)}"
            )
        for delta in self.deltas:
            mark = "worse" if delta.worse else "ok"
            lines.append(
                f"  {delta.name}: trial {_fmt_metric(delta.name, delta.trial)} · "
                f"preset {_fmt_metric(delta.name, delta.baseline)} · {mark}"
            )
        if self.worst_pairs:
            worst = self.worst_pairs[0]
            lines.append(f"worst pair {worst.text} min optical gap {worst.min_gap:.1f}")
        overridden = tuple(g.char for g in self.glyphs if g.overridden and g.char in WEAK_GLYPHS)
        lines.append("weak overrides: " + (", ".join(overridden) if overridden else "(none)"))
        for gap in self.l0_gaps:
            lines.append(f"L0: {gap}")
        for failure in self.failures:
            lines.append(f"fail: {failure}")
        if self.charset_failures:
            lines.append(f"charset gate: {len(self.charset_failures)} issue(s) (report only until M2)")
            for msg in self.charset_failures[:8]:
                lines.append(f"  charset: {msg}")
            if len(self.charset_failures) > 8:
                lines.append(f"  charset: … and {len(self.charset_failures) - 8} more")
        if self.sequence_failures:
            lines.append(
                f"DesignSequence: {len(self.sequence_failures)} issue(s)"
            )
            for msg in self.sequence_failures[:8]:
                lines.append(f"  sequence: {msg}")
            if len(self.sequence_failures) > 8:
                lines.append(
                    f"  sequence: … and {len(self.sequence_failures) - 8} more"
                )
        for note in self.notes:
            lines.append(f"note: {note}")
        return "\n".join(lines)

    def write_json(self, path: Path | str) -> Path:
        destination = Path(path)
        destination.parent.mkdir(parents=True, exist_ok=True)
        payload = asdict(self)
        payload["worst_pairs"] = [asdict(pair) for pair in self.worst_pairs]
        payload["sentence_text"] = AGENT_SENTENCE
        payload["pairs_expected"] = list(AGENT_PAIRS)
        destination.write_text(
            json.dumps(payload, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        return destination


def design_review(
    controls: Controls,
    *,
    baseline: Controls | None = None,
    out_dir: Path | str | None = None,
) -> DesignReview:
    """Score ``controls`` against ``baseline`` and optionally write preview PNGs.

    ``baseline`` should be ``Controls.from_context(the_preset_you_started_from)``,
    not a heavier or lighter master. L0 also requires two weak-glyph overrides.
    """
    sentence = controls_sentence_report(controls, AGENT_SENTENCE)
    pairs = controls_pair_gaps(controls)
    glyphs = _glyph_scores(controls)
    deltas: tuple[MetricDelta, ...] = ()
    notes: list[str] = []
    baseline_report = None
    if baseline is None:
        notes.append(
            "no preset baseline; L1 compares optical ratio and G1 to "
            "Controls.from_context(preset())"
        )
    else:
        baseline_report = controls_sentence_report(baseline, AGENT_SENTENCE)
        deltas = _deltas(sentence, baseline_report)
    failures = collect_gate_failures(
        sentence,
        baseline_report=baseline_report,
        pairs=pairs,
    )
    l0_gaps = _l0_gaps(controls)
    charset_failures = tuple(collect_family_gate_failures(controls))
    sequence_failures = _body_sequence_failures(controls)
    notes.extend(_spec_notes(controls))
    review = DesignReview(
        sentence=sentence,
        failures=failures,
        pairs=pairs,
        deltas=deltas,
        glyphs=glyphs,
        l0_gaps=l0_gaps,
        charset_failures=charset_failures,
        sequence_failures=sequence_failures,
        notes=tuple(notes),
    )
    if out_dir is not None:
        notes.extend(_write_artifacts(controls, review, Path(out_dir), baseline=baseline))
        review = DesignReview(
            sentence=review.sentence,
            failures=review.failures,
            pairs=review.pairs,
            deltas=review.deltas,
            glyphs=review.glyphs,
            l0_gaps=review.l0_gaps,
            charset_failures=review.charset_failures,
            sequence_failures=review.sequence_failures,
            notes=tuple(notes),
        )
    return review



def _body_sequence_failures(controls: Controls) -> tuple[str, ...]:
    """Run designer-order body + digit unlock; empty means stock is consistent."""
    from typekernel.qa.design_sequence import (
        DesignSequenceError,
        unlock_controls_body,
        unlock_controls_digits,
    )

    out: list[str] = []
    try:
        unlock_controls_body(controls)
    except DesignSequenceError as exc:
        hints = tuple(exc.hints[:6])
        out.extend((f"body DesignSequence: {exc}", *hints))
    try:
        unlock_controls_digits(controls)
    except DesignSequenceError as exc:
        hints = tuple(exc.hints[:6])
        out.extend((f"digit DesignSequence: {exc}", *hints))
    return tuple(out)


def _fmt_metric(name: str, value: float) -> str:
    if "g1" in name:
        return str(round(value))
    return f"{value:.3f}"


def _deltas(trial: WordReport, baseline: WordReport) -> tuple[MetricDelta, ...]:
    trial_g1 = float(non_terminal_g1(trial))
    base_g1 = float(non_terminal_g1(baseline))
    return (
        MetricDelta(
            "optical_gap_ratio",
            trial.optical_gap_ratio,
            baseline.optical_gap_ratio,
            worse=trial.optical_gap_ratio > baseline.optical_gap_ratio + RELATIVE_RATIO_SLACK,
        ),
        MetricDelta(
            "non_terminal_g1",
            trial_g1,
            base_g1,
            worse=trial_g1 > base_g1,
        ),
        MetricDelta(
            "stem_cv",
            trial.stem_cv,
            baseline.stem_cv,
            # Shown in the delta table only. The gate does not fail on stem CV
            # relative to the preset; absolute SentenceGateLimits still apply.
            worse=trial.stem_cv > baseline.stem_cv + RELATIVE_RATIO_SLACK,
        ),
    )


def _spec_notes(controls: Controls) -> list[str]:
    return [f"spec {ch}: {asdict(controls.glyph_specs[ch])}" for ch in sorted(controls.glyph_specs)]


def _weak_overrides(controls: Controls) -> tuple[str, ...]:
    return tuple(
        ch
        for ch in WEAK_GLYPHS
        if ch in controls.glyph_overrides or ch in controls.glyph_specs
    )


def _l0_gaps(controls: Controls) -> tuple[str, ...]:
    overridden = _weak_overrides(controls)
    if len(overridden) >= L0_MIN_WEAK_OVERRIDES:
        return ()
    have = ", ".join(overridden) if overridden else "none"
    listed = "".join(WEAK_GLYPHS)
    return (
        f"need >={L0_MIN_WEAK_OVERRIDES} with_glyph/tuned_glyph overrides among {listed}; "
        + f"have {have}",
    )


def _glyph_scores(controls: Controls) -> tuple[GlyphScore, ...]:
    charset = "".join(dict.fromkeys("".join(REVIEW_GLYPHS) + "no"))
    drawn = polish_glyph_map(
        controls.build_all(charset),
        GlyphPolishOptions(joins_policy="tangent_fix"),
    )
    scores: list[GlyphScore] = []
    for char in REVIEW_GLYPHS:
        smoothness = join_smoothness_glyph(drawn[char])
        scores.append(
            GlyphScore(
                char=char,
                g1_errors=int(smoothness.detail["error_count"]),
                overridden=char in controls.glyph_overrides or char in controls.glyph_specs,
            )
        )
    return tuple(scores)


def _preview_outline(glyph: ComposedGlyph) -> Outline:
    contours = tuple(
        contour for outline in (*glyph.solids, *glyph.holes) for contour in outline.contours
    )
    return Outline(contours)


def _write_artifacts(
    controls: Controls,
    review: DesignReview,
    out_dir: Path,
    *,
    baseline: Controls | None = None,
) -> list[str]:
    notes: list[str] = []
    out_dir.mkdir(parents=True, exist_ok=True)
    review.write_json(out_dir / "review.json")
    notes.append(f"review json: {out_dir / 'review.json'}")
    artifact_paths: dict[str, Path] = {"review_json": out_dir / "review.json"}
    try:
        from typekernel.qa.sheet import contact_sheet, diff_overlay, review_index
        from typekernel.qa.specimen_png import render_outline_png
    except ImportError as exc:
        notes.append(f"review artifacts skipped: {exc}")
        return notes
    contact = contact_sheet(controls, out_dir / "contact.png")
    artifact_paths["contact"] = contact
    notes.append(f"contact sheet: {contact.name}")
    if baseline is not None:
        diff = diff_overlay(
            controls,
            baseline,
            out_dir / "diff.png",
            chars="mutj&#!$",
        )
        artifact_paths["diff"] = diff
        notes.append(f"diff overlay: {diff.name}")
    drawn = controls.build_all("".join(dict.fromkeys("".join(REVIEW_GLYPHS))))
    for char in REVIEW_GLYPHS:
        destination = out_dir / f"{char}.png"
        render_outline_png(_preview_outline(drawn[char]), destination, size=256)
        artifact_paths[f"glyph_{char}"] = destination
        notes.append(f"control png: {destination.name}")
    index = review_index(out_dir, artifact_paths)
    notes.append(f"review index: {index.name}")
    return notes
