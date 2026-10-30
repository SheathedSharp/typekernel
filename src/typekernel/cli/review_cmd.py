"""``tk review`` / ``tk status`` / ``tk critique``."""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from pathlib import Path

from typekernel.project import open_project
from typekernel.review.critique import critique_project, format_critique
from typekernel.review.records import open_review, record_review
from typekernel.review.status import format_status, status_board

__all__ = [
    "critique_text",
    "parse_expect_changes",
    "parse_reads_as",
    "review_open",
    "review_record",
    "status_project",
]


def review_open(path: str | Path, group: str, *, reviewer: str = "agent:unknown") -> Path:
    with open_project(path) as session:
        rec = open_review(session, group, reviewer=reviewer)
        dest = Path(session.root) / "reviews" / f"{group}-r{rec.round}.json"
        return dest


def review_record(
    path: str | Path,
    group: str,
    *,
    verdict: str,
    note: str = "",
    reviewer: str = "agent:unknown",
    proofs: Sequence[str] | None = None,
    proof_paths: Sequence[str | Path] | None = None,
    reads_as: Mapping[str, str] | None = None,
    require_reads_as: bool = False,
    expect_changes: Sequence[str] | None = None,
) -> Path:
    with open_project(path) as session:
        rec = record_review(
            session,
            group,
            verdict=verdict,  # type: ignore[arg-type]
            note=note,
            reviewer=reviewer,
            proofs=proofs,
            proof_paths=proof_paths,
            reads_as=reads_as,
            require_reads_as=require_reads_as,
            expect_changes=expect_changes,
        )
        return Path(session.root) / "reviews" / f"{group}-r{rec.round}.json"


def status_project(path: str | Path) -> str:
    with open_project(path) as session:
        return format_status(status_board(session))


def critique_text(
    path: str | Path,
    text: str,
    *,
    master: str | None = None,
    as_json: bool = False,
) -> str:
    report = critique_project(path, text, master=master)
    return format_critique(report, as_json=as_json)


def parse_reads_as(raw: str | None) -> dict[str, str] | None:
    """Parse ``--reads-as`` JSON object ``{"z": "z", ...}``."""
    if raw is None or not str(raw).strip():
        return None
    data = json.loads(raw)
    if not isinstance(data, dict):
        raise TypeError("--reads-as must be a JSON object of glyph→label")
    return {str(k): str(v) for k, v in data.items()}


def parse_expect_changes(raw: Sequence[str] | None) -> list[str] | None:
    """Collect ``--expect-change`` rationale strings."""
    if not raw:
        return None
    out = [str(x).strip() for x in raw if str(x).strip()]
    return out or None
