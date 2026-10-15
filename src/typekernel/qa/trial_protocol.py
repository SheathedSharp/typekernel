"""Agent trial protocol (DEVELOPMENT_PLAN §6) — fixed briefs and recorded metrics."""

from __future__ import annotations

import json
from collections.abc import Sequence
from dataclasses import asdict, dataclass
from pathlib import Path

from typekernel.parts import Controls, DesignContext
from typekernel.parts.weight_relief import STEM_RELIEF_ONSET
from typekernel.qa.family_gate import collect_family_gate_failures
from typekernel.qa.identity import check_identity_controls
from typekernel.qa.lint import lint_controls
from typekernel.qa.originality import (
    L3_VOICE_DISTANCE_THRESHOLD,
    nearest_voice_distance,
)

WEIGHT_LADDER_STEMS = (30.0, 70.0, 110.0, 150.0, 180.0)

__all__ = [
    "FIXED_TRIAL_BRIEFS",
    "L3_VOICE_DISTANCE_THRESHOLD",
    "TrialBrief",
    "TrialSnapshot",
    "snapshot_trial",
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
        "Editorial geometric sans (single-storey a/g; slab deferred per D2)",
        "geometric_sans",
        notes="Editorial brief may use slab_serif() or bracketed_serif() presets (TK-306).",
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
    weight_ladder_r8_failures: int
    glyph_spec_chars: tuple[str, ...]
    cheating_flags: tuple[str, ...]

    @property
    def family_gate_ok(self) -> bool:
        return not self.family_gate_failures

    @property
    def metrics_ok(self) -> bool:
        return self.lint_error_count == 0 and self.identity_error_count == 0

    @property
    def l3_voice_ok(self) -> bool:
        return self.voice_distance >= L3_VOICE_DISTANCE_THRESHOLD


def voice_distance(controls: Controls) -> float:
    """Distance to the nearest built-in preset (see ``qa.originality``)."""
    return nearest_voice_distance(controls)


def weight_ladder_r8_failures(ctx: DesignContext) -> int:
    """Count ladder stems where R8 fails on the counter-pinch charset."""
    failures = 0
    for stem in WEIGHT_LADDER_STEMS:
        sheet = Controls.from_context(ctx.tuned(stem=stem))
        if stem >= STEM_RELIEF_ONSET:
            sheet = sheet.with_stem_relief()
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
    return TrialSnapshot(
        brief_id=brief.id,
        preset=brief.preset,
        apis_used=_api_tags(controls, apis_used),
        round=round,
        family_gate_failures=tuple(collect_family_gate_failures(controls)),
        lint_error_count=len(lint_report.errors),
        identity_error_count=len(identity_report.errors),
        voice_distance=voice_distance(controls),
        weight_ladder_r8_failures=weight_ladder_r8_failures(controls.context),
        glyph_spec_chars=tuple(sorted(controls.glyph_specs)),
        cheating_flags=tuple(cheating_flags),
    )


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
