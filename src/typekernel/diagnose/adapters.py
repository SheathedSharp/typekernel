"""Adapt plugins.checks CheckFn into diagnose Check protocol v2."""

from __future__ import annotations

from collections.abc import Iterable

from typekernel.diagnose.protocol import CheckContext, Finding, Scope, legacy_finding
from typekernel.plugins.checks.protocol import CheckContext as LegacyContext
from typekernel.plugins.checks.protocol import CheckFn
from typekernel.plugins.checks.protocol import Finding as LegacyFinding

__all__ = ["LegacyCheck", "wrap_check_fn"]


class LegacyCheck:
    """Wrap a side-effecting ``CheckFn`` as a ``Check`` with fixed id/scope."""

    def __init__(self, fn: CheckFn, *, check_id: str, scope: Scope = "glyph") -> None:
        self._fn = fn
        self.id = check_id
        self.scope: Scope = scope

    def run(self, ctx: CheckContext) -> Iterable[Finding]:
        if ctx.name is None or ctx.raw is None or ctx.final is None:
            return []
        bucket: list[LegacyFinding] = []
        legacy = LegacyContext(
            name=ctx.name,
            raw=ctx.raw,
            final=ctx.final,
            system=ctx.system,
            project=ctx.project,
            stem_kinds=ctx.stem_kinds,
            declared_stems=ctx.declared_stems,
            findings=bucket,
            session=ctx.session,
        )
        self._fn(legacy)
        out: list[Finding] = []
        for f in bucket:
            out.append(
                legacy_finding(
                    f.kind,
                    f.level,
                    f.glyph,
                    f.message,
                    master=ctx.master,
                )
            )
        return out


def wrap_check_fn(fn: CheckFn, *, check_id: str, scope: Scope = "glyph") -> LegacyCheck:
    return LegacyCheck(fn, check_id=check_id, scope=scope)
