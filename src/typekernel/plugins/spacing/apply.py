"""Apply Abs sidebearing suggestions into Metrics / project spacing.py.

Dry-run by default. Contours are never edited — only Metrics keys become Abs.
On-disk writes require ``write=True`` and target ``<project>/spacing.py``.
"""

from __future__ import annotations

import json
import re
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass
from pathlib import Path

from typekernel.metrics import Metrics, with_abs_sidebearings
from typekernel.plugins.spacing.protocol import SidebearingSuggestion, SpacingSuggestions
from typekernel.project.session import ProjectSession

__all__ = [
    "ApplyPlan",
    "ApplyPlanEntry",
    "ApplyResult",
    "build_apply_plan",
    "metrics_after_plan",
    "run_apply",
    "write_apply_plan",
    "write_spacing_py_abs",
]


@dataclass(frozen=True, slots=True)
class ApplyPlanEntry:
    glyph: str
    lsb: float
    rsb: float
    previous: str
    method: str


@dataclass(frozen=True, slots=True)
class ApplyPlan:
    entries: tuple[ApplyPlanEntry, ...]
    dry_run: bool


@dataclass(frozen=True, slots=True)
class ApplyResult:
    plan: ApplyPlan
    plan_path: Path
    written_glyphs: tuple[str, ...]
    spacing_py: Path | None


def _side_repr(side: object) -> str:
    cls = type(side).__name__
    if hasattr(side, "value"):
        return f"{cls}({side.value})"
    if hasattr(side, "key"):
        return f"{cls}({side.key!r})"
    return cls


def build_apply_plan(
    session: ProjectSession,
    suggestions: SpacingSuggestions | Sequence[SidebearingSuggestion],
    *,
    dry_run: bool = True,
) -> ApplyPlan:
    """Build a plan of Abs overlays from sidebearing suggestions."""
    if isinstance(suggestions, SpacingSuggestions):
        sides = suggestions.sidebearings
    else:
        sides = tuple(suggestions)
    metrics = session.project.metrics
    entries: list[ApplyPlanEntry] = []
    for s in sides:
        prev = "missing"
        if metrics is not None and s.glyph in metrics.keys:
            a, b = metrics.keys[s.glyph]
            prev = f"{_side_repr(a)}, {_side_repr(b)}"
        entries.append(
            ApplyPlanEntry(
                glyph=s.glyph,
                lsb=float(s.lsb),
                rsb=float(s.rsb),
                previous=prev,
                method=s.method,
            )
        )
    return ApplyPlan(entries=tuple(entries), dry_run=bool(dry_run))


def metrics_after_plan(session: ProjectSession, plan: ApplyPlan) -> Metrics:
    """Return Metrics with Abs keys from ``plan`` (pure merge; no I/O)."""
    base = session.project.metrics or Metrics()
    updates = {e.glyph: (e.lsb, e.rsb) for e in plan.entries}
    return with_abs_sidebearings(base, updates)


def write_apply_plan(plan: ApplyPlan, path: str | Path) -> Path:
    """Serialize the plan JSON (always safe; no project mutation)."""
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "note": (
            "Spacing apply plan — Abs sidebearings for Project.metrics. "
            "dry_run=true means spacing.py was NOT modified. Contours untouched."
        ),
        "dry_run": plan.dry_run,
        "entries": [asdict(e) for e in plan.entries],
    }
    out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return out


_KEY_LINE = re.compile(
    r"""^(?P<indent>\s*)(?P<quote>['"])(?P<name>[^'"]+)(?P=quote)\s*:\s*\([^)]*\)\s*,(?P<rest>\s*(?:#.*)?)?$"""
)


def write_spacing_py_abs(
    spacing_py: Path,
    updates: Mapping[str, tuple[float, float]],
) -> list[str]:
    """Rewrite matching ``METRICS`` key lines to ``Abs(lsb), Abs(rsb)``.

    Ensures ``Abs`` is imported from ``typekernel.metrics``. Glyphs already
    present as key lines are rewritten in place; new glyphs are inserted just
    before the ``space=`` / ``space =`` argument of ``Metrics(...)``.
    Returns the list of glyph names written.
    """
    if not updates:
        return []
    text = spacing_py.read_text(encoding="utf-8")
    text = _ensure_abs_import(text)

    changed: list[str] = []
    out_lines: list[str] = []
    for raw in text.splitlines(keepends=True):
        stripped_nl = raw.rstrip("\n")
        m = _KEY_LINE.match(stripped_nl)
        if m and m.group("name") in updates:
            name = m.group("name")
            lsb, rsb = updates[name]
            indent = m.group("indent")
            q = m.group("quote")
            rest = m.group("rest") or ""
            out_lines.append(
                f"{indent}{q}{name}{q}: (Abs({lsb:g}), Abs({rsb:g})),{rest}\n"
            )
            changed.append(name)
        else:
            out_lines.append(raw if raw.endswith("\n") else raw + "\n")

    missing = [n for n in updates if n not in changed]
    if missing:
        insert = "".join(
            f"        '{n}': (Abs({updates[n][0]:g}), Abs({updates[n][1]:g})),\n"
            for n in missing
        )
        joined = "".join(out_lines)
        placed = False
        for mark in ("\n    space=", "\n    space =", "\n    pack=", "\n    pack ="):
            if mark in joined:
                joined = joined.replace(mark, "\n" + insert + mark.lstrip("\n"), 1)
                placed = True
                break
        if not placed:
            raise ValueError(
                f"could not insert Abs keys {missing}; no Metrics space=/pack= marker"
            )
        spacing_py.write_text(joined, encoding="utf-8")
        changed.extend(missing)
        return changed

    spacing_py.write_text("".join(out_lines), encoding="utf-8")
    return changed


def _ensure_abs_import(text: str) -> str:
    if "from typekernel.metrics import" in text:
        # single-line import only
        lines = text.splitlines(keepends=True)
        for i, line in enumerate(lines):
            if line.startswith("from typekernel.metrics import"):
                if "Abs" in line:
                    return text
                # insert Abs after import keyword
                lines[i] = line.replace(
                    "from typekernel.metrics import ",
                    "from typekernel.metrics import Abs, ",
                    1,
                )
                return "".join(lines)
        return text
    lines = text.splitlines(keepends=True)
    insert_at = 0
    for i, line in enumerate(lines):
        if line.startswith("from __future__"):
            insert_at = i + 1
            break
    lines.insert(insert_at, "from typekernel.metrics import Abs, Metrics\n")
    return "".join(lines)


def run_apply(
    session: ProjectSession,
    suggestions: SpacingSuggestions | Sequence[SidebearingSuggestion],
    *,
    out: str | Path,
    write: bool = False,
) -> ApplyResult:
    """Build plan, always write plan JSON; rewrite spacing.py only if ``write``.

    Contours are never touched. ``write=False`` (default) is a dry-run.
    """
    plan = build_apply_plan(session, suggestions, dry_run=not write)
    plan_path = write_apply_plan(plan, out)
    written: list[str] = []
    spacing_py: Path | None = None
    if write and plan.entries:
        spacing_py = Path(session.root) / "spacing.py"
        if not spacing_py.is_file():
            raise FileNotFoundError(
                f"cannot --write Abs metrics: missing {spacing_py}"
            )
        updates = {e.glyph: (e.lsb, e.rsb) for e in plan.entries}
        written = write_spacing_py_abs(spacing_py, updates)
    return ApplyResult(
        plan=plan,
        plan_path=plan_path,
        written_glyphs=tuple(written),
        spacing_py=spacing_py if write else None,
    )
