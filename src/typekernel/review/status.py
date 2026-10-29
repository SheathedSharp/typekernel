"""``tk status`` task board (target §8.2)."""

from __future__ import annotations

from dataclasses import dataclass, field

from typekernel.diagnose import audit_project
from typekernel.project.session import ProjectSession
from typekernel.review.records import is_stale, latest_pass

__all__ = ["GroupStatus", "StatusBoard", "format_status", "status_board"]


@dataclass
class GroupStatus:
    group: str
    glyphs_done: int
    glyphs_total: int
    errors: int
    warnings: int
    review: str  # pass rN / fail rN / stale (...) / -
    masters: str


@dataclass
class StatusBoard:
    family: str
    charset_done: int
    charset_total: int
    masters: int
    groups: list[GroupStatus] = field(default_factory=list)
    release_gate: str = ""


def status_board(session: ProjectSession) -> StatusBoard:
    project = session.project
    specs = session.specs()
    # Groups from policy or GlyphSpec.group.
    groups_map: dict[str, list[str]] = dict(project.review.groups)
    if not groups_map:
        for name, spec in specs.items():
            g = spec.group or name
            groups_map.setdefault(g, []).append(name)

    report = audit_project(session.root)
    err_by: dict[str, int] = {}
    warn_by: dict[str, int] = {}
    for f in report.findings:
        if not f.glyph or f.glyph == "*":
            continue
        # glyph may be "a/b" for pairs — attribute to first.
        gname = f.glyph.split("/")[0]
        if f.level == "error":
            err_by[gname] = err_by.get(gname, 0) + 1
        elif f.level == "warn":
            warn_by[gname] = warn_by.get(gname, 0) + 1

    group_rows: list[GroupStatus] = []
    unreviewed = 0
    for group, names in sorted(groups_map.items()):
        names = [n for n in names if n in specs]
        e = sum(err_by.get(n, 0) for n in names)
        w = sum(warn_by.get(n, 0) for n in names)
        passed = latest_pass(session, group)
        stale, changed = is_stale(session, group)
        if passed is None:
            review = "-"
            unreviewed += 1
        elif stale:
            review = f"stale ({','.join(changed[:4])})"
            unreviewed += 1
        else:
            review = f"{passed.verdict} r{passed.round}"
        group_rows.append(
            GroupStatus(
                group=group,
                glyphs_done=len(names),
                glyphs_total=len(names),
                errors=e,
                warnings=w,
                review=review,
                masters="ok" if project.masters else "-",
            )
        )

    approvals_dir = session.root / "approvals"
    human_ok = 0
    if approvals_dir.is_dir():
        for path in approvals_dir.glob("*.json"):
            try:
                import json

                data = json.loads(path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                continue
            if data.get("approved") is True and str(data.get("approver", "")).startswith(
                "human:"
            ):
                human_ok += 1

    if unreviewed or human_ok == 0:
        gate = (
            f"blocked ({unreviewed} groups not passed, "
            f"{human_ok} human approvals)"
        )
    else:
        gate = "open"

    return StatusBoard(
        family=project.info.family,
        charset_done=len(specs),
        charset_total=len(specs),
        masters=len(project.masters),
        groups=group_rows,
        release_gate=gate,
    )


def format_status(board: StatusBoard) -> str:
    lines = [
        (
            f"{board.family}          charset {board.charset_done}/{board.charset_total}  "
            f"masters {board.masters}"
        ),
        f"{'group':12} {'glyphs':8} {'E':3} {'W':3} {'review':18} masters",
    ]
    for g in board.groups:
        lines.append(
            f"{g.group:12} {g.glyphs_done}/{g.glyphs_total:<6} "
            f"{g.errors:<3} {g.warnings:<3} {g.review:18} {g.masters}"
        )
    lines.append(f"release gate: {board.release_gate}")
    return "\n".join(lines)
