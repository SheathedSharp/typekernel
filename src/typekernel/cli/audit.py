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
from types import ModuleType
from typing import Any

from typekernel.cli.load import load_project
from typekernel.plugins.checks import builtin_checks
from typekernel.plugins.checks.protocol import CheckContext, CheckFn, Finding, raw_drawing
from typekernel.system.intent import Intent

__all__ = [
    "AuditReport",
    "Finding",
    "audit_project",
    "format_report",
    "load_audit_stems",
    "load_intent",
]

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


def _load_system_module(root: Path) -> ModuleType | None:
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
    except Exception:  # noqa: BLE001 - optional metadata must not break audit
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

    Allowed kinds: ``vertical``, ``diagonal``. Glyphs omitted from the map
    get no optical stem kinds (named nodes only).
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


def load_extra_checks(root: Path) -> tuple[CheckFn, ...]:
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


def load_intent(root: Path) -> Intent | None:
    """Load optional ``BRIEF`` / ``INTENT`` from the project's ``system.py``.

    Returns an :class:`~typekernel.system.intent.Intent` or ``None``. Accepts
    ``Brief``, ``Intent``, or a mapping of Intent fields.
    """
    from typekernel.system.intent import coerce_intent

    module = _load_system_module(root)
    if module is None:
        return None
    raw = getattr(module, "BRIEF", None)
    if raw is None:
        raw = getattr(module, "INTENT", None)
    return coerce_intent(raw)


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
    """Resolve optical stem kinds for ``name``.

    Kernel default is empty (named-node measurements only). Projects opt in
    per glyph via ``AUDIT_STEMS``. The legacy ``"auto"`` token is accepted
    as an alias for empty — there is no letter-name auto policy anymore.
    """
    if name in declared:
        kinds = tuple(declared[name])
        if kinds == ("auto",):
            return ()
        return kinds
    return ()


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
    Optional ``BRIEF`` / ``INTENT`` is checked once against ``System``
    (:mod:`typekernel.system.intent`) — warnings only, not aesthetics AI.
    """
    root_path = Path(root).resolve()
    project = load_project(root_path)
    project.discover()
    names = glyphs if glyphs is not None else sorted(project.specs())
    report = AuditReport(glyphs=len(names))
    stem_kinds = load_audit_stems(root_path)

    # Project-level intent check (once): prose Brief / typed Intent vs System.
    intent = load_intent(root_path)
    if intent is not None:
        from typekernel.system.intent import check_intent

        for mismatch in check_intent(project.system, intent):
            report.findings.append(
                Finding(
                    kind="intent",
                    level=mismatch.level,
                    glyph="*",
                    message=f"{mismatch.field}: {mismatch.message}",
                )
            )
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
            declared_stems=stem_kinds,
            findings=report.findings,
        )
        for fn in checks:
            fn(ctx)

    return report


def format_report(report: AuditReport) -> str:
    lines = [
        (
            f"tk audit: {report.glyphs} glyphs, "
            f"{len(report.errors)} errors, {len(report.warnings)} warnings"
        )
    ]
    for f in report.findings:
        lines.append(f"  [{f.level}] {f.kind} {f.glyph}: {f.message}")
    if not report.findings:
        lines.append("  (no findings)")
    return "\n".join(lines)
