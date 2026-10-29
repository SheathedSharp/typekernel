"""``tk review`` / ``tk status``."""

from __future__ import annotations

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
) -> Path:
    with open_project(path) as session:
        rec = record_review(
            session, group, verdict=verdict, note=note, reviewer=reviewer  # type: ignore[arg-type]
        )
        return Path(session.root) / "reviews" / f"{group}-r{rec.round}.json"


def status_project(path: str | Path) -> str:
    with open_project(path) as session:
        return format_status(status_board(session))
