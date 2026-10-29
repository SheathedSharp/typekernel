"""Info-level tag grammar check (ARCHITECTURE.md 标签语法)."""

from __future__ import annotations

from collections.abc import Iterable

from typekernel.anatomy.tags import is_valid_tag
from typekernel.diagnose.protocol import CheckContext, Finding, Scope

__all__ = ["TagsGrammarCheck"]


class TagsGrammarCheck:
    """Report node / slot tags that do not match the normative grammar."""

    id = "tags.grammar"
    scope: Scope = "glyph"

    def run(self, ctx: CheckContext) -> Iterable[Finding]:
        if ctx.name is None or ctx.raw is None:
            return []
        drawing = ctx.raw
        seen: set[str] = set()
        bad: list[str] = []
        for group in drawing.nodes:
            for node in group:
                tag = node.tag
                if not tag or tag in seen:
                    continue
                seen.add(tag)
                if not is_valid_tag(tag):
                    bad.append(tag)
        for slot in drawing.slots:
            tag = slot.tag
            if not tag or tag in seen:
                continue
            seen.add(tag)
            if not is_valid_tag(tag):
                bad.append(tag)
        out: list[Finding] = []
        for tag in sorted(bad):
            out.append(
                Finding(
                    check="tags.grammar",
                    level="info",
                    glyph=ctx.name,
                    master=ctx.master,
                    where=tag,
                    measured=tag,
                    expected="part(.qualifier)*",
                    message=f"tag {tag!r} does not match anatomy tag grammar",
                    hint="see ARCHITECTURE.md 标签语法; rename toward stem.l.foot.o etc.",
                )
            )
        return out
