"""Audit engine v2 — run checks, baselines, JSON (target §7)."""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

from typekernel.diagnose.adapters import wrap_check_fn
from typekernel.diagnose.baseline import Baseline, load_baseline
from typekernel.diagnose.protocol import Check, CheckContext, Finding
from typekernel.plugins.checks.protocol import raw_drawing
from typekernel.project import open_project
from typekernel.qa.outline_hash import outline_hash
from typekernel.system.intent import Intent
from typekernel.system.lint import lint_per_glyph_metric_tokens

__all__ = [
    "AuditReport",
    "audit_project",
    "format_report",
    "kinds_for",
    "load_audit_stems",
    "load_extra_checks",
    "load_intent",
]


@dataclass
class AuditReport:
    findings: list[Finding] = field(default_factory=list)
    glyphs: int = 0
    masters: tuple[str | None, ...] = (None,)

    @property
    def errors(self) -> list[Finding]:
        return [f for f in self.findings if f.level == "error"]

    @property
    def warnings(self) -> list[Finding]:
        return [f for f in self.findings if f.level == "warn"]

    def to_dict(self) -> dict[str, Any]:
        return {
            "glyphs": self.glyphs,
            "masters": [m for m in self.masters],
            "errors": len(self.errors),
            "warnings": len(self.warnings),
            "findings": [f.to_dict() for f in self.findings],
        }




def load_audit_stems(root: Path) -> Mapping[str, Sequence[str]]:
    """Load stem kinds from ``Project.audit.stems``."""
    from typekernel.project import open_project

    with open_project(root) as session:
        return {str(k): tuple(v) for k, v in session.project.audit.stems.items()}


def load_extra_checks(root: Path) -> tuple[Any, ...]:
    """Load ``Project.audit.extra_checks``."""
    from typekernel.project import open_project

    try:
        with open_project(root) as session:
            return tuple(session.project.audit.extra_checks)
    except Exception:  # noqa: BLE001
        return ()


def load_intent(root: Path) -> Intent | None:
    """Load intent from ``Project.brief``."""
    from typekernel.project import open_project
    from typekernel.system.intent import coerce_intent

    try:
        with open_project(root) as session:
            brief = session.project.brief
            if brief is not None:
                return coerce_intent(brief)
    except Exception:  # noqa: BLE001 — empty scaffold / pre-migration
        return None
    return None



def kinds_for(name: str, declared: Mapping[str, Sequence[str]]) -> tuple[str, ...]:
    if name in declared:
        kinds = tuple(declared[name])
        if kinds == ("auto",):
            return ()
        return kinds
    return ()


def _builtin_v2(
    *,
    check_stem: bool,
    check_zone: bool,
    check_direction: bool,
    check_compat: bool,
    check_overlap: bool,
    check_topology: bool = True,
    check_vertical: bool = True,
    check_spacing: bool = True,
    check_gray: bool = True,
    check_interpolation: bool = True,
) -> list[Check]:
    from typekernel.diagnose.checks.anchors import AnchorsCheck
    from typekernel.diagnose.checks.contour import ContourQualityCheck
    from typekernel.diagnose.checks.features import FeaturesSyntaxCheck
    from typekernel.diagnose.checks.gray import GrayCheck
    from typekernel.diagnose.checks.interpolation import InterpolationCheck
    from typekernel.diagnose.checks.spacing import (
        PairCollisionCheck,
        RefConsistencyCheck,
        SpacingCheck,
    )
    from typekernel.diagnose.checks.tags import TagsGrammarCheck
    from typekernel.diagnose.checks.topology import TopologyCheck
    from typekernel.diagnose.checks.vertical import VerticalCheck
    from typekernel.plugins.checks import compat, direction, overlap, stem, zone

    out: list[Check] = []
    if check_direction:
        out.append(wrap_check_fn(direction.check, check_id="direction"))
    if check_stem:
        out.append(wrap_check_fn(stem.check, check_id="stem"))
    if check_zone:
        out.append(wrap_check_fn(zone.check, check_id="zone"))
    if check_compat:
        out.append(wrap_check_fn(compat.check, check_id="compat"))
    if check_overlap:
        out.append(wrap_check_fn(overlap.check, check_id="overlap"))
    if check_topology:
        out.append(TopologyCheck())
        out.append(ContourQualityCheck())
    if check_vertical:
        out.append(VerticalCheck())
    if check_spacing:
        out.append(SpacingCheck())
        out.append(PairCollisionCheck())
        out.append(RefConsistencyCheck())
    if check_gray:
        out.append(GrayCheck())
    if check_interpolation:
        out.append(InterpolationCheck())
    # Anchors + tag grammar always on; letter-free / data-driven.
    out.append(AnchorsCheck())
    out.append(FeaturesSyntaxCheck())
    out.append(TagsGrammarCheck())
    return out


def audit_project(
    root: str | Path,
    *,
    glyphs: list[str] | None = None,
    check_stem: bool = True,
    check_zone: bool = True,
    check_direction: bool = True,
    check_compat: bool = True,
    check_overlap: bool = False,
    check_topology: bool = True,
    check_vertical: bool = True,
    check_spacing: bool = True,
    check_gray: bool = True,
    check_interpolation: bool = True,
    masters: Sequence[str] | None = None,
    baseline: Path | str | Baseline | None = None,
    extra_checks: Sequence[Check] | None = None,
) -> AuditReport:
    """Run diagnose v2 over a project; return structured findings."""
    root_path = Path(root).resolve()
    baseline_obj: Baseline | None = None
    if isinstance(baseline, Baseline):
        baseline_obj = baseline
    elif baseline is not None:
        baseline_obj = load_baseline(baseline)
    else:
        default_bl = root_path / "audit-baseline.json"
        if default_bl.is_file():
            baseline_obj = load_baseline(default_bl)

    with open_project(root_path) as session:
        project = session.project
        from typekernel.project.scope import scoped_glyph_names
        names = glyphs if glyphs is not None else scoped_glyph_names(session)
        master_list: list[str | None]
        if masters is None:
            master_list = [None]
        elif len(masters) == 1 and masters[0] == "all":
            master_list = [m.name for m in project.masters] or [None]
        else:
            master_list = list(masters)

        report = AuditReport(glyphs=len(names), masters=tuple(master_list))
        stem_kinds = {str(k): tuple(v) for k, v in project.audit.stems.items()}

        intent = None
        if project.brief is not None:
            intent = project.brief.intent
        if intent is not None:
            from typekernel.system.intent import check_intent

            for mismatch in check_intent(project.system, intent):
                lvl = mismatch.level
                level: Literal["error", "warn", "info"]
                if lvl == "error":
                    level = "error"
                elif lvl == "info":
                    level = "info"
                else:
                    level = "warn"
                report.findings.append(
                    Finding(
                        check="intent",
                        level=level,
                        glyph="*",
                        master=None,
                        where=mismatch.field,
                        measured=None,
                        expected=None,
                        message=mismatch.message,
                    )
                )

        for token in lint_per_glyph_metric_tokens(project.system):
            report.findings.append(
                Finding(
                    check="system",
                    level="warn",
                    glyph="*",
                    master=None,
                    where=token,
                    measured=None,
                    expected=None,
                    message=(
                        f"token {token!r} looks like a per-glyph width/advance; "
                        "move it to project elements (or metrics) — "
                        "System.tokens keeps only global controls "
                        "(n_width/o_width/H_width/O_width)"
                    ),
                )
            )

        checks: list[Check] = _builtin_v2(
            check_stem=check_stem,
            check_zone=check_zone,
            check_direction=check_direction,
            check_compat=check_compat,
            check_overlap=check_overlap,
            check_topology=check_topology,
            check_vertical=check_vertical,
            check_spacing=check_spacing,
            check_gray=check_gray,
            check_interpolation=check_interpolation,
        )
        # Project EXTRA_CHECKS (legacy CheckFn) + diagnose Check objects.
        legacy_extras = (
            list(project.audit.extra_checks)
            if project.audit.extra_checks
            else list(load_extra_checks(root_path))
        )
        for i, fn in enumerate(legacy_extras):
            if hasattr(fn, "id") and hasattr(fn, "run"):
                checks.append(fn)
            else:
                checks.append(wrap_check_fn(fn, check_id=f"extra.{i}"))
        if extra_checks:
            checks.extend(extra_checks)

        hashes: dict[str, str] = {}
        for master in master_list:
            system = project.system
            if master is not None:
                by = {m.name: m for m in project.masters}
                if master in by:
                    system = by[master].system
            for name in names:
                raw = raw_drawing(session, name, master=master)
                final = session.evaluate(name, master=master).drawing
                hashes[name] = outline_hash(final.outline())
                resolved = {name: kinds_for(name, stem_kinds)}
                ctx = CheckContext(
                    session=session,
                    project=project,
                    system=system,
                    master=master,
                    name=name,
                    raw=raw,
                    final=final,
                    stem_kinds=resolved,
                    declared_stems=stem_kinds,
                )
                for check in checks:
                    if check.scope == "glyph":
                        report.findings.extend(list(check.run(ctx)))
                    elif check.scope in {"font", "family"} and name == names[0]:
                        # Run once per master for font-scope.
                        report.findings.extend(list(check.run(ctx)))

        if baseline_obj is not None:
            report.findings = baseline_obj.filter(report.findings, hashes=hashes)
        return report


def format_report(report: AuditReport, *, as_json: bool = False) -> str:
    if as_json:
        return json.dumps(report.to_dict(), indent=2, sort_keys=True)
    lines = [
        (
            f"tk audit: {report.glyphs} glyphs, "
            f"{len(report.errors)} errors, {len(report.warnings)} warnings"
        )
    ]
    for f in report.findings:
        g = f.glyph or "*"
        master = f"@{f.master}" if f.master else ""
        lines.append(f"  [{f.level}] {f.check} {g}{master}: {f.message}")
    if not report.findings:
        lines.append("  (no findings)")
    return '\n'.join(lines)
