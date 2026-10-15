"""Agent trial protocol (DEVELOPMENT_PLAN §6) — fixed briefs and recorded metrics."""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass, replace
from pathlib import Path

from typekernel.parts import Controls, DesignContext
from typekernel.parts.weight_relief import STEM_RELIEF_ONSET
from typekernel.qa.family_gate import collect_family_gate_failures
from typekernel.qa.identity import check_identity_controls
from typekernel.qa.lint import lint_controls
from typekernel.qa.originality import (
    L3_MIN_TOPOLOGY_FRACTION,
    L3_VOICE_DISTANCE_THRESHOLD,
    l3_voice_criteria_met,
    nearest_voice_distance,
    topology_fraction_vs_nearest_presets,
)

WEIGHT_LADDER_STEMS = (30.0, 70.0, 110.0, 150.0, 180.0, 200.0)

__all__ = [
    "FIXED_TRIAL_BRIEFS",
    "L3_VOICE_DISTANCE_THRESHOLD",
    "TrialBrief",
    "TrialSnapshot",
    "controls_at_ladder_stem",
    "l3_voice_criteria_met",
    "snapshot_trial",
    "trial_snapshot_exit_code",
    "validate_trial_snapshot",
    "validate_trial_snapshot_record",
    "voice_distance",
    "weight_ladder_r8_failures",
    "write_trial_snapshot",
]


@dataclass(frozen=True, slots=True)
class TrialBrief:
    """One of the three frozen agent briefs (do not edit after a trial starts)."""

    id: str
    title: str
    preset: str
    notes: str = ""


FIXED_TRIAL_BRIEFS: tuple[TrialBrief, ...] = (
    TrialBrief(
        "brief-1",
        "Warm humanist UI sans (Regular + Bold)",
        "humanist_sans",
    ),
    TrialBrief(
        "brief-2",
        "Editorial geometric sans (single-storey a/g; or slab/bracketed serif voices)",
        "geometric_sans",
        notes="Serif trials: slab_serif() / bracketed_serif() presets (TK-306); snapshot_serif_voices.py.",
    ),
    TrialBrief(
        "brief-3",
        "Coding clear with full ASCII punctuation",
        "code_clear",
    ),
)


@dataclass(frozen=True, slots=True)
class TrialSnapshot:
    """Machine-readable trial record (human scores added in AGENT_TRIALS.md)."""

    brief_id: str
    preset: str
    apis_used: tuple[str, ...]
    round: int
    family_gate_failures: tuple[str, ...]
    lint_error_count: int
    identity_error_count: int
    voice_distance: float
    topology_fraction: float
    weight_ladder_r8_failures: int
    glyph_spec_chars: tuple[str, ...]
    cheating_flags: tuple[str, ...]
    l3_voice_ok: bool

    @property
    def family_gate_ok(self) -> bool:
        return not self.family_gate_failures

    @property
    def metrics_ok(self) -> bool:
        return self.lint_error_count == 0 and self.identity_error_count == 0


def voice_distance(controls: Controls) -> float:
    """Distance to the nearest built-in preset (see ``qa.originality``)."""
    return nearest_voice_distance(controls)


def controls_at_ladder_stem(template: Controls, stem: float) -> Controls:
    """Rebuild ``template`` at another stem (keeps ``Style``, specs, overrides)."""
    ctx = template.context.tuned(stem=stem)
    sheet = Controls.from_context(ctx, style=template.style)
    sheet = replace(
        sheet,
        glyph_specs=dict(template.glyph_specs),
        glyph_overrides=dict(template.glyph_overrides),
    )
    if stem >= STEM_RELIEF_ONSET:
        sheet = sheet.with_stem_relief()
    return sheet


def weight_ladder_r8_failures(controls: Controls | DesignContext) -> int:
    """Count ladder stems where R8 fails on the counter-pinch charset."""
    template = (
        controls
        if isinstance(controls, Controls)
        else Controls.from_context(controls)
    )
    failures = 0
    for stem in WEIGHT_LADDER_STEMS:
        sheet = controls_at_ladder_stem(template, stem)
        report = lint_controls(sheet, counter_min=True)
        if any(i.rule == "R8_counter_min" for i in report.issues):
            failures += 1
    return failures


def _api_tags(controls: Controls, extra: Sequence[str] = ()) -> tuple[str, ...]:
    tags: list[str] = list(extra)
    if controls.glyph_specs:
        tags.append("tuned_glyph")
    if controls.glyph_overrides and not controls.glyph_specs:
        tags.append("with_glyph")
    if controls.context.stem >= STEM_RELIEF_ONSET:
        tags.append("with_stem_relief")
    return tuple(dict.fromkeys(tags))


def _infer_cheating_flags(controls: Controls) -> tuple[str, ...]:
    """TK-307/502: high voice_distance with no topology change (e.g. stem-only scale)."""
    voice_distance_val = voice_distance(controls)
    topology = topology_fraction_vs_nearest_presets(controls)
    if (
        voice_distance_val >= L3_VOICE_DISTANCE_THRESHOLD
        and topology < L3_MIN_TOPOLOGY_FRACTION
    ):
        return ("stem_only_or_scale_voice",)
    return ()


def snapshot_trial(
    controls: Controls,
    *,
    brief: TrialBrief,
    round: int = 1,
    apis_used: Sequence[str] = (),
    cheating_flags: Sequence[str] = (),
) -> TrialSnapshot:
    """Capture lint/identity/gate metrics for one trial sheet."""
    charset = controls.supported
    lint_report = lint_controls(controls, charset)
    identity_report = check_identity_controls(controls, charset)
    merged_flags = tuple(dict.fromkeys((*cheating_flags, *_infer_cheating_flags(controls))))
    return TrialSnapshot(
        brief_id=brief.id,
        preset=brief.preset,
        apis_used=_api_tags(controls, apis_used),
        round=round,
        family_gate_failures=tuple(collect_family_gate_failures(controls)),
        lint_error_count=len(lint_report.errors),
        identity_error_count=len(identity_report.errors),
        voice_distance=voice_distance(controls),
        topology_fraction=topology_fraction_vs_nearest_presets(controls),
        weight_ladder_r8_failures=weight_ladder_r8_failures(controls),
        glyph_spec_chars=tuple(sorted(controls.glyph_specs)),
        cheating_flags=merged_flags,
        l3_voice_ok=l3_voice_criteria_met(controls),
    )


def _snapshot_float(value: object, default: float = 0.0) -> float:
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        return float(value)
    return default


def validate_trial_snapshot_record(data: Mapping[str, object]) -> tuple[str, ...]:
    """Program checks on a written snapshot JSON (TK-502 final validation review)."""
    problems: list[str] = []
    voice_distance_val = _snapshot_float(data.get("voice_distance"), 0.0)
    topology = _snapshot_float(data.get("topology_fraction"), 0.0)
    l3_ok = bool(data.get("l3_voice_ok"))
    if l3_ok and voice_distance_val < L3_VOICE_DISTANCE_THRESHOLD:
        problems.append("l3_voice_ok but voice_distance below L3_VOICE_DISTANCE_THRESHOLD")
    if l3_ok and topology < L3_MIN_TOPOLOGY_FRACTION:
        problems.append("l3_voice_ok but topology_fraction below L3_MIN_TOPOLOGY_FRACTION")
    if (
        not l3_ok
        and voice_distance_val >= L3_VOICE_DISTANCE_THRESHOLD
        and topology >= L3_MIN_TOPOLOGY_FRACTION
    ):
        problems.append(
            "voice_distance and topology_fraction pass but l3_voice_ok is false (gate/lint?)"
        )
    return tuple(problems)


def validate_trial_snapshot(snapshot: TrialSnapshot) -> tuple[str, ...]:
    """Validate a :class:`TrialSnapshot` before claiming TK-502 program pass."""
    return validate_trial_snapshot_record(
        {
            "voice_distance": snapshot.voice_distance,
            "topology_fraction": snapshot.topology_fraction,
            "l3_voice_ok": snapshot.l3_voice_ok,
        }
    )


def trial_snapshot_exit_code(
    snapshot: TrialSnapshot,
    problems: tuple[str, ...] = (),
) -> int:
    """CLI exit codes for ``snapshot_design.py`` / ``snapshot_reference_trials.py``."""
    if not snapshot.metrics_ok:
        return 2
    if not snapshot.family_gate_ok:
        return 3
    if snapshot.weight_ladder_r8_failures:
        return 4
    if problems:
        return 5
    if snapshot.cheating_flags:
        return 7
    if not snapshot.l3_voice_ok:
        return 6
    return 0


def write_trial_snapshot(path: Path | str, snapshot: TrialSnapshot) -> Path:
    """Write JSON snapshot; create parent directories."""
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    payload = asdict(snapshot)
    payload["family_gate_ok"] = snapshot.family_gate_ok
    payload["metrics_ok"] = snapshot.metrics_ok
    payload["l3_voice_ok"] = snapshot.l3_voice_ok
    destination.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return destination
