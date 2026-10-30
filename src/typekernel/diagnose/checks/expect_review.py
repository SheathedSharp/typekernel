"""S5: expect.py edits need expect_changes rationale in a review record."""

from __future__ import annotations

import json
from collections.abc import Iterable
from pathlib import Path

from typekernel.diagnose.protocol import CheckContext, Finding, Scope

__all__ = ["ExpectChangesCheck"]


class ExpectChangesCheck:
    """Warn when expect is non-empty, reviews exist, and none cite expect_changes.

    Stock starters ship ``expect.py`` with no ``reviews/`` yet — stay quiet so
    ``tk audit`` 0/0 is preserved. Once the designer records reviews, every
    non-empty expect table needs at least one ``expect_changes`` rationale.
    """

    id = "expect.changes"
    scope: Scope = "font"

    def run(self, ctx: CheckContext) -> Iterable[Finding]:
        expect = ctx.project.expect or {}
        if not expect:
            return []
        reviews_dir = Path(ctx.session.root) / "reviews"
        if not reviews_dir.is_dir():
            return []
        review_files = list(reviews_dir.glob("*-r*.json"))
        if not review_files:
            return []
        rationales = 0
        for path in review_files:
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                continue
            changes = data.get("expect_changes") or []
            if changes:
                rationales += 1
        if rationales:
            return []
        return [
            Finding(
                check="expect.changes",
                level="warn",
                glyph=None,
                master=ctx.master,
                where="expect.py",
                measured=len(expect),
                expected="review.expect_changes",
                message=(
                    f"project expect declares {len(expect)} entries and reviews "
                    "exist, but no review record lists expect_changes rationale"
                ),
                hint=(
                    "tk review record … --expect-change 'why' "
                    "(or expect_changes in the review JSON)"
                ),
            )
        ]
