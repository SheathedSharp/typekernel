"""``tk audit`` — stem / zone / direction / master-compat diagnostics (ARCH 验收方式).

Reports are diagnostic by default. Structural errors (wrong contour direction,
master signature mismatch) raise the process exit code. Stem / zone deviations
are warnings for the designer to fix in glyph code.

Built-in checks live in ``typekernel.plugins.checks``; projects may append
``EXTRA_CHECKS`` in ``system.py``.
"""

from __future__ import annotations

import importlib.util
import sys
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from typekernel.cli.load import load_project
from typekernel.plugins.checks import builtin_checks
from typekernel.plugins.checks.protocol import CheckContext, Finding, raw_drawing
from typekernel.project import Project

__all__ = ["AuditReport", "Finding", "audit_project", "format_report", "load_audit_stems"]

# Glyphs that rarely carry upright stems; optical vertical probes on these are
# usually measuring diagonals or bowls. Projects may override via AUDIT_STEMS.
_DEFAULT_NON_VERTICAL = frozenset(
    {
        "v",
        "w",
        "x",
        "y",
        "z",
        "V",
        "W",
        "X",
        "Y",
        "Z",
        "s",
        "S",
        "e",
        "c",
        "o",
        "O",
        "a",
        "A",
        "k",
        "K",
        "Q",
        "R",
        "G",
        "C",
    }
)

# Diagonal-primary letters: default optical probe is oriented (not vertical),
# so sans does not flood with "vertical stem on a diagonal" noise, but italic /
# diagonal projects still get measure_oriented_stem without declaring AUDIT_STEMS.
_DEFAULT_DIAGONAL = frozenset(
    {
        "v",
        "w",
        "x",
        "y",
        "z",
        "V",
        "W",
        "X",
        "Y",
        "Z",
    }
)


@dataclass
class AuditReport:
    findings: list[Finding] = field(default_factory=list)
    glyphs: int = 0

    @property
    def errors(self) -> list[Finding]:
        return [f for f in self.findings if f.level == "error"]

    @property
    def warnings(self) -> list[Finding]:
        return [f for f in self.findings if f.level == "warn"]


def _load_system_module(root: Path):
    system_py = root / "system.py"
    if not system_py.is_file():
        return None
    root_s = str(root.resolve())
    if root_s not in sys.path:
        sys.path.insert(0, root_s)
    mod_name = f"_typekernel_user_system_audit_{abs(hash(root_s)) & 0xFFFFFFFF:x}"
    spec = importlib.util.spec_from_file_location(mod_name, system_py)
    if spec is None or spec.loader is None:
        return None
    module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)
    except Exception:
        return None
    return module


def load_audit_stems(root: Path) -> Mapping[str, Sequence[str]]:
    """Load optional ``AUDIT_STEMS`` from the project's ``system.py``.

    Values are stroke-kind tokens per glyph::

        AUDIT_STEMS = {
            "n": ("vertical",),
            "v": ("diagonal",),
            "w": (),            # named nodes only; no optical fallback
            "x": "none",        # alias for ()
        }

    Allowed kinds: ``vertical``, ``diagonal``. Unknown keys fall back to the
    built-in auto policy in :func:`_kinds_for`.
    """
    module = _load_system_module(root)
    if module is None:
        return {}
    raw = getattr(module, "AUDIT_STEMS", None)
    if raw is None or not isinstance(raw, Mapping):
        return {}
    out: dict[str, tuple[str, ...]] = {}
    for key, value in raw.items():
        out[str(key)] = _normalize_kinds(value)
    return out


def load_extra_checks(root: Path) -> tuple:
    """Load optional ``EXTRA_CHECKS`` callables from ``system.py``."""
    module = _load_system_module(root)
    if module is None:
        return ()
    raw = getattr(module, "EXTRA_CHECKS", None) or getattr(module, "CHECKS", None)
    if raw is None:
        return ()
    if callable(raw):
        return (raw,)
    return tuple(raw)


def _normalize_kinds(value: Any) -> tuple[str, ...]:
    if value is None or value == "none" or value == ():
        return ()
    if isinstance(value, str):
        if value in {"vertical", "diagonal"}:
            return (value,)
        if value == "auto":
            return ("auto",)
        return ()
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        kinds = []
        for item in value:
            s = str(item)
            if s in {"vertical", "diagonal"}:
                kinds.append(s)
        return tuple(kinds)
    return ()


def _kinds_for(name: str, declared: Mapping[str, Sequence[str]]) -> tuple[str, ...]:
    if name in declared:
        kinds = tuple(declared[name])
        if kinds == ("auto",):
            return _auto_kinds(name)
        return kinds
    return _auto_kinds(name)


def _auto_kinds(name: str) -> tuple[str, ...]:
    """Default optical policy when the project does not declare AUDIT_STEMS.

    Letters without upright stems skip optical **vertical** probes (the
    historical false-noise source). Diagonal-primary letters
    (``v w x y z`` and caps) default to oriented ``diagonal`` probes via
    ``measure_oriented_stem`` — quiet on upright sans, useful when stems are
    truly diagonal. Bowl letters (``o e c s …``) stay silent unless the
    project opts in via ``AUDIT_STEMS``.
    """
    if name in _DEFAULT_DIAGONAL:
        return ("diagonal",)
    if name in _DEFAULT_NON_VERTICAL:
        return ()
    return ("vertical",)


def audit_project(
    root: str | Path,
    *,
    glyphs: list[str] | None = None,
    check_stem: bool = True,
    check_zone: bool = True,
    check_direction: bool = True,
    check_compat: bool = True,
    check_overlap: bool = False,
) -> AuditReport:
    """Run named-node / outline audits on a project; return a structured report.

    ``check_overlap`` is opt-in: pairwise ink∩ink is filtered to cancels that
    adjoin a declared counter (字腔 notch under even-odd). Pure multi-ink
    overlap without counters stays quiet. Pass True (CLI ``--overlap``) when
    hunting cavity defects on bowls with overlapping stems.

    Project ``system.py`` may define ``EXTRA_CHECKS`` (or ``CHECKS``) as a
    sequence of ``CheckFn`` callables appended after the built-ins.
    """
    root_path = Path(root).resolve()
    project = load_project(root_path)
    project.discover()
    names = glyphs if glyphs is not None else sorted(project.specs())
    report = AuditReport(glyphs=len(names))
    stem_kinds = load_audit_stems(root_path)
    checks = list(
        builtin_checks(
            check_stem=check_stem,
            check_zone=check_zone,
            check_direction=check_direction,
            check_compat=check_compat,
            check_overlap=check_overlap,
        )
    )
    checks.extend(load_extra_checks(root_path))

    for name in names:
        raw = raw_drawing(project, name)
        final = project.evaluate(name)
        resolved = {name: _kinds_for(name, stem_kinds)}
        ctx = CheckContext(
            name=name,
            raw=raw,
            final=final,
            system=project.system,
            project=project,
            stem_kinds=resolved,
            findings=report.findings,
        )
        for fn in checks:
            fn(ctx)

    return report


def format_report(report: AuditReport) -> str:
    lines = [
        f"tk audit: {report.glyphs} glyphs, "
        f"{len(report.errors)} errors, {len(report.warnings)} warnings"
    ]
    for f in report.findings:
        lines.append(f"  [{f.level}] {f.kind} {f.glyph}: {f.message}")
    if not report.findings:
        lines.append("  (no findings)")
    return "\n".join(lines)
