"""``tk review`` / ``tk status``."""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from pathlib import Path

from typekernel.project import open_project
from typekernel.review.records import open_review, record_review
from typekernel.review.status import format_status, status_board

__all__ = ["review_open", "review_record", "status_project"]


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
        )
        return Path(session.root) / "reviews" / f"{group}-r{rec.round}.json"


def status_project(path: str | Path) -> str:
    with open_project(path) as session:
        return format_status(status_board(session))


def parse_reads_as(raw: str | None) -> dict[str, str] | None:
    """Parse ``--reads-as`` JSON object ``{"z": "z", ...}``."""
    if raw is None or not str(raw).strip():
        return None
    data = json.loads(raw)
    if not isinstance(data, dict):
        raise TypeError("--reads-as must be a JSON object of glyph→label")
    return {str(k): str(v) for k, v in data.items()}
