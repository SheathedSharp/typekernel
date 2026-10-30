"""S5 ``tk critique`` — objective self-score table (not human aesthetics).

Aggregates S0 evidence, S1 contour, S2 read/ID, and S3 join/gap signals for a
project + text string so ACCEPTANCE self-critique can cite one command.
"""

from __future__ import annotations

import json
import statistics
from collections.abc import Sequence
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Literal

from typekernel.diagnose.checks.join import run_text_join_audit
from typekernel.font.glyph import glyph_name_for_char
from typekernel.metrics.join import Join, measure_text_joins
from typekernel.perceive.read import ReadReport, read_text
from typekernel.plugins.checks.protocol import raw_drawing
from typekernel.project import open_project
from typekernel.project.session import ProjectSession
from typekernel.review.records import ReviewRecord, is_agent_reviewer

__all__ = [
    "CritiqueReport",
    "CritiqueRow",
    "critique_project",
    "format_critique",
]

Level = Literal["ok", "warn", "fail", "info", "n/a"]


@dataclass(frozen=True, slots=True)
class CritiqueRow:
    """One objective score line."""

    signal: str
    level: Level
    score: float | None
    """Normalized 0–1 when meaningful; None for n/a."""

    detail: str
    source: str
    """Which slice produced the signal (S0/S1/S2/S3)."""


@dataclass
class CritiqueReport:
    text: str
    rows: list[CritiqueRow] = field(default_factory=list)
    glyphs: int = 0
    read_reports: list[ReadReport] = field(default_factory=list)

    @property
    def warns(self) -> list[CritiqueRow]:
        return [r for r in self.rows if r.level == "warn"]

    @property
    def fails(self) -> list[CritiqueRow]:
        return [r for r in self.rows if r.level == "fail"]

    def to_dict(self) -> dict[str, Any]:
        return {
            "text": self.text,
            "glyphs": self.glyphs,
            "rows": [asdict(r) for r in self.rows],
            "warns": len(self.warns),
            "fails": len(self.fails),
        }


def _letters(text: str) -> list[str]:
    return [ch for ch in text if not ch.isspace()]


def _s2_read_rows(reports: Sequence[ReadReport]) -> list[CritiqueRow]:
    rows: list[CritiqueRow] = []
    hard = 0
    covered = 0
    for r in reports:
        if r.top:
            covered += 1
        hard += sum(1 for w in r.warnings if w.level == "warn")
    n = len(reports) or 1
    score = max(0.0, 1.0 - hard / n)
    level: Level = "ok" if hard == 0 else "warn"
    if covered == 0 and reports:
        level = "fail"
        score = 0.0
    rows.append(
        CritiqueRow(
            signal="read.identity",
            level=level,
            score=score,
            detail=f"{covered}/{len(reports)} glyphs read; {hard} hard warn(s)",
            source="S2",
        )
    )
    confuse = sum(
        1
        for r in reports
        for w in r.warnings
        if w.level == "warn" and "confuse-pair" in w.message
    )
    if confuse:
        rows.append(
            CritiqueRow(
                signal="read.confuse",
                level="warn",
                score=max(0.0, 1.0 - confuse / n),
                detail=f"{confuse} confuse-pair hard warn(s)",
                source="S2",
            )
        )
    return rows


def _s3_join_rows(session: ProjectSession, text: str) -> list[CritiqueRow]:
    from typekernel.font.glyph import Glyph

    glyphs: dict[str, Glyph] = {}
    for ch in _letters(text):
        try:
            name = glyph_name_for_char(ch)
        except ValueError:
            continue
        if name in glyphs or name not in session.specs():
            continue
        try:
            glyphs[name] = session.glyph(name)
        except Exception:  # noqa: BLE001, S112
            continue
    policy = Join()
    if session.project.metrics is not None and session.project.metrics.join is not None:
        policy = session.project.metrics.join
    measures, cv = measure_text_joins(glyphs, text, use_join_advance=True)
    joined = [m for m in measures if m.has_join]
    rows: list[CritiqueRow] = []
    if not measures:
        rows.append(
            CritiqueRow(
                signal="join.coverage",
                level="n/a",
                score=None,
                detail="no adjacent pairs in text",
                source="S3",
            )
        )
        return rows
    if joined:
        max_dy = max(m.dy for m in joined)
        dy_ok = max_dy <= policy.max_dy
        rows.append(
            CritiqueRow(
                signal="join.dy",
                level="ok" if dy_ok else "warn",
                score=1.0 if dy_ok else max(0.0, 1.0 - (max_dy - policy.max_dy) / max(policy.max_dy, 1.0)),
                detail=f"max Δy={max_dy:.1f} (threshold {policy.max_dy}); {len(joined)} joined pairs",
                source="S3",
            )
        )
        cv_ok = cv <= policy.max_gap_cv
        rows.append(
            CritiqueRow(
                signal="join.rhythm_cv",
                level="ok" if cv_ok else "warn",
                score=1.0 if cv_ok else max(0.0, 1.0 - (cv - policy.max_gap_cv)),
                detail=f"gap CV={cv:.3f} (threshold {policy.max_gap_cv})",
                source="S3",
            )
        )
        gaps = [m.gap for m in joined]
        rows.append(
            CritiqueRow(
                signal="join.gap_dist",
                level="info",
                score=None,
                detail=(
                    f"gaps n={len(gaps)} mean={statistics.fmean(gaps):.2f} "
                    f"stdev={statistics.pstdev(gaps) if len(gaps) > 1 else 0.0:.2f} "
                    f"min={min(gaps):.2f} max={max(gaps):.2f}"
                ),
                source="S3",
            )
        )
    else:
        # No entry/exit — still report spacing outliers via text join audit.
        findings = run_text_join_audit(session, text, policy=policy, use_join_advance=False)
        outliers = [f for f in findings if f.check == "join.spacing_outlier"]
        missing = [f for f in findings if f.check == "join.missing"]
        rows.append(
            CritiqueRow(
                signal="join.anchors",
                level="info",
                score=None,
                detail=f"{len(missing)} pairs without entry/exit; spacing outliers={len(outliers)}",
                source="S3",
            )
        )
        if outliers:
            rows.append(
                CritiqueRow(
                    signal="join.spacing_outlier",
                    level="warn",
                    score=max(0.0, 1.0 - len(outliers) / max(len(measures), 1)),
                    detail=f"{len(outliers)} absolute gap outlier(s)",
                    source="S3",
                )
            )
    return rows


def _s1_contour_rows(session: ProjectSession, text: str) -> list[CritiqueRow]:
    from typekernel.diagnose.checks.contour import ContourQualityCheck
    from typekernel.diagnose.protocol import CheckContext

    names: list[str] = []
    for ch in _letters(text):
        try:
            gn = glyph_name_for_char(ch)
        except ValueError:
            continue
        if gn in session.specs() and gn not in names:
            names.append(gn)
    check = ContourQualityCheck()
    warns = 0
    infos = 0
    for name in names:
        raw = raw_drawing(session, name)
        final = session.evaluate(name).drawing
        ctx = CheckContext(
            session=session,
            project=session.project,
            system=session.project.system,
            name=name,
            raw=raw,
            final=final,
        )
        for f in check.run(ctx):
            if f.level == "warn":
                warns += 1
            elif f.level == "info":
                infos += 1
    n = len(names) or 1
    level: Level = "ok" if warns == 0 else "warn"
    return [
        CritiqueRow(
            signal="contour.quality",
            level=level,
            score=max(0.0, 1.0 - warns / n),
            detail=f"{warns} contour warn(s), {infos} info across {len(names)} glyphs",
            source="S1",
        )
    ]


def _s0_evidence_rows(session: ProjectSession) -> list[CritiqueRow]:
    rows: list[CritiqueRow] = []
    # Scan all review groups lightly: any pass with proof evidence.
    reviews_dir = Path(session.root) / "reviews"
    passes = 0
    agent_unverified = 0
    humanish = 0
    if reviews_dir.is_dir():
        for path in reviews_dir.glob("*-r*.json"):
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                rec = ReviewRecord.from_dict(data)
            except (json.JSONDecodeError, KeyError, TypeError, ValueError):
                continue
            if rec.verdict != "pass":
                continue
            passes += 1
            if is_agent_reviewer(rec.reviewer) and not rec.has_proof_evidence:
                agent_unverified += 1
            if rec.has_proof_evidence:
                humanish += 1
    if passes == 0:
        rows.append(
            CritiqueRow(
                signal="evidence.review",
                level="info",
                score=None,
                detail="no pass reviews yet (S0 evidence gate idle)",
                source="S0",
            )
        )
    else:
        level: Level = "ok" if humanish else "warn"
        rows.append(
            CritiqueRow(
                signal="evidence.review",
                level=level,
                score=1.0 if humanish else 0.4,
                detail=(
                    f"{passes} pass record(s); {humanish} with proof hashes; "
                    f"{agent_unverified} agent-pass without proofs"
                ),
                source="S0",
            )
        )
    # expect_changes coverage
    expect = session.project.expect or {}
    expect_py = Path(session.root) / "expect.py"
    if expect or expect_py.is_file():
        review_files: list[Path] = []
        if reviews_dir.is_dir():
            review_files = list(reviews_dir.glob("*-r*.json"))
        rationales = 0
        for path in review_files:
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                if data.get("expect_changes"):
                    rationales += 1
            except (json.JSONDecodeError, TypeError, OSError):
                continue
        if expect and review_files and rationales == 0:
            rows.append(
                CritiqueRow(
                    signal="expect.changes",
                    level="warn",
                    score=0.0,
                    detail=(
                        f"project declares {len(expect)} expect entries and "
                        f"{len(review_files)} review(s) exist, but none list "
                        "expect_changes rationale"
                    ),
                    source="S5",
                )
            )
        else:
            exp_level: Level = "ok" if (not expect or rationales or not review_files) else "info"
            score = 1.0 if (not expect or rationales) else None
            if expect and not review_files:
                exp_level = "info"
                score = None
            rows.append(
                CritiqueRow(
                    signal="expect.changes",
                    level=exp_level,
                    score=score,
                    detail=(
                        f"expect keys={len(expect)}; reviews={len(review_files)}; "
                        f"with expect_changes={rationales}"
                    ),
                    source="S5",
                )
            )
    return rows


def critique_project(
    root: str | Path,
    text: str,
    *,
    master: str | None = None,
) -> CritiqueReport:
    """Build an objective critique table for ``text`` against the project."""
    del master  # reserved for multi-master critique
    root_path = Path(root).resolve()
    with open_project(root_path) as session:
        reports = read_text(session, text)
        rows: list[CritiqueRow] = []
        rows.extend(_s0_evidence_rows(session))
        rows.extend(_s1_contour_rows(session, text))
        rows.extend(_s2_read_rows(reports))
        rows.extend(_s3_join_rows(session, text))
        return CritiqueReport(
            text=text,
            rows=rows,
            glyphs=len({r.glyph for r in reports}),
            read_reports=list(reports),
        )


def format_critique(report: CritiqueReport, *, as_json: bool = False) -> str:
    """Human table or JSON for ``tk critique``."""
    if as_json:
        return json.dumps(report.to_dict(), indent=2) + "\n"
    lines = [
        (
            f"tk critique: text={report.text!r} glyphs={report.glyphs} "
            f"warns={len(report.warns)} fails={len(report.fails)}"
        ),
        f"{'signal':<22} {'lvl':<5} {'score':>5}  detail",
        "-" * 72,
    ]
    for r in report.rows:
        score = f"{r.score:.2f}" if r.score is not None else "  n/a"
        lines.append(f"{r.signal:<22} {r.level:<5} {score:>5}  [{r.source}] {r.detail}")
    lines.append("")
    lines.append(
        "Note: scores are objective program signals (S0–S3/S5), not human "
        "readable/unified/distinctive/complete marks."
    )
    return "\n".join(lines) + "\n"
