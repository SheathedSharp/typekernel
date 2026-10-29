"""features.syntax — feaLib validation of assembled feature text."""

from __future__ import annotations

from collections.abc import Iterable

from typekernel.diagnose.protocol import CheckContext, Finding, Scope
from typekernel.features import FeatureSyntaxError, assemble_features, validate_fea

__all__ = ["FeaturesSyntaxCheck"]


class FeaturesSyntaxCheck:
    id = "features.syntax"
    scope: Scope = "font"

    def run(self, ctx: CheckContext) -> Iterable[Finding]:
        project = ctx.project
        session = ctx.session
        names = set(session.specs()) | set(project.composites)
        text = assemble_features(
            names,
            fea_dir=project.features.fea_dir,
            root=session.root,
            extra=tuple(project.features.extra),
        )
        try:
            validate_fea(text)
        except FeatureSyntaxError as exc:
            where = None
            if exc.path or exc.line:
                where = f"{exc.path or '<assembled>'}:{exc.line or '?'}"
            return [
                Finding(
                    check="features.syntax",
                    level="error",
                    glyph=None,
                    master=ctx.master,
                    where=where,
                    measured=None,
                    expected=None,
                    message=str(exc),
                    hint="fix features/*.fea or suffix naming; see feaLib error",
                )
            ]
        return []
