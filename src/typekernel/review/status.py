"""``tk status`` task board (target §8.2)."""

from __future__ import annotations

from dataclasses import dataclass, field

from typekernel.diagnose import audit_project
from typekernel.project.session import ProjectSession
from typekernel.review.records import is_stale, latest_pass

__all__ = [
    "BlockCoverage",
    "GroupStatus",
    "StatusBoard",
    "format_status",
    "status_board",
]


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
class BlockCoverage:
    block: str
    done: int
    total: int


@dataclass
class StatusBoard:
    family: str
    charset_done: int
    charset_total: int
    masters: int
    groups: list[GroupStatus] = field(default_factory=list)
    blocks: list[BlockCoverage] = field(default_factory=list)
    release_gate: str = ""


_BLOCKS: tuple[tuple[str, int, int], ...] = (
    ("Basic Latin", 0x0020, 0x007E),
    ("Latin-1 Supplement", 0x00A0, 0x00FF),
    ("Latin Extended-A", 0x0100, 0x017F),
)


def _covered_codepoints(session: ProjectSession) -> set[int]:
    from typekernel.project.evaluate import unicodes_for_glyph_name

    covered: set[int] = set()
    for name, spec in session.specs().items():
        if spec.unicodes is None:
            covered.update(unicodes_for_glyph_name(name))
        else:
            covered.update(spec.unicodes)
    for name, comp in session.project.composites.items():
        if comp.unicodes is None:
            covered.update(unicodes_for_glyph_name(name))
        else:
            covered.update(comp.unicodes)
    return covered


def _charset_totals(
    session: ProjectSession,
) -> tuple[int, int, list[BlockCoverage]]:
    project = session.project
    covered = _covered_codepoints(session)
    if project.charset is None:
        n = len(session.specs()) + len(project.composites)
        return n, n, []
    cps = project.charset.codepoints
    extra = project.charset.extra_names
    names_have = set(session.specs()) | set(project.composites)
    extra_done = sum(1 for n in extra if n in names_have)
    done = sum(1 for cp in cps if cp in covered) + extra_done
    total = len(cps) + len(extra)
    blocks: list[BlockCoverage] = []
    for label, lo, hi in _BLOCKS:
        block_cps = [cp for cp in cps if lo <= cp <= hi]
        if not block_cps:
            continue
        blocks.append(
            BlockCoverage(
                block=label,
                done=sum(1 for cp in block_cps if cp in covered),
                total=len(block_cps),
            )
        )
    return done, total, blocks


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
        elif passed.verdict == "pass" and (
            not str(passed.reviewer).startswith("human:")
            or not passed.has_proof_evidence
        ):
            # S0: agent self-pass (even with proof hashes) is visible but
            # does not clear the exit gate — only human approvals do.
            review = f"agent-pass (unverified) r{passed.round}"
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

    charset_done, charset_total, blocks = _charset_totals(session)
    return StatusBoard(
        family=project.info.family,
        charset_done=charset_done,
        charset_total=charset_total,
        masters=len(project.masters),
        groups=group_rows,
        blocks=blocks,
        release_gate=gate,
    )


def format_status(board: StatusBoard) -> str:
    lines = [
        (
            f"{board.family}          charset {board.charset_done}/{board.charset_total}  "
            f"masters {board.masters}"
        ),
    ]
    if board.blocks:
        lines.append("unicode blocks:")
        for b in board.blocks:
            lines.append(f"  {b.block:22} {b.done}/{b.total}")
    lines.append(
        f"{'group':12} {'glyphs':8} {'err':3} {'wrn':3} {'review':18} masters"
    )
    for g in board.groups:
        lines.append(
            f"{g.group:12} {g.glyphs_done}/{g.glyphs_total:<6} "
            f"{g.errors:<3} {g.warnings:<3} {g.review:18} {g.masters}"
        )
    lines.append(f"release gate: {board.release_gate}")
    return "\n".join(lines)
