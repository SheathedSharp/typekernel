"""Anchor checks: mark attachment points and composite mark@anchor refs."""

from __future__ import annotations

from collections.abc import Iterable

from typekernel.diagnose.protocol import CheckContext, Finding, Scope

__all__ = ["AnchorsCheck"]


def _attachment_anchors(names: Iterable[str]) -> list[str]:
    return [n for n in names if n.startswith("_")]


class AnchorsCheck:
    """Mark glyphs need a ``_<name>`` attachment; composites must resolve."""

    id = "anchors"
    scope: Scope = "font"

    def run(self, ctx: CheckContext) -> Iterable[Finding]:
        out: list[Finding] = []
        session = ctx.session
        project = ctx.project
        specs = session.specs()

        # Collect glyph anchors from evaluated drafts (cheaper than full Font).
        anchor_names: dict[str, set[str]] = {}
        for name, spec in specs.items():
            try:
                draft = session.evaluate(name, master=ctx.master, slots=True)
            except Exception as exc:  # noqa: BLE001 - surface as diagnose finding
                out.append(
                    Finding(
                        check="anchors.evaluate",
                        level="error",
                        glyph=name,
                        master=ctx.master,
                        where=None,
                        measured=None,
                        expected=None,
                        message=f"failed to evaluate for anchor check: {exc}",
                        hint="fix the glyph builder, then re-audit",
                    )
                )
                continue
            anchor_names[name] = set(draft.anchors)

            traits = set(spec.traits)
            if (
                "mark" in traits
                and "spacing-mark" not in traits
                and not _attachment_anchors(draft.anchors)
            ):
                    out.append(
                        Finding(
                            check="anchors.mark_attachment",
                            level="error",
                            glyph=name,
                            master=ctx.master,
                            where=None,
                            measured=None,
                            expected="_top|_bottom|_ogonek|…",
                            message=(
                                f"mark glyph {name!r} has no attachment anchor "
                                "(name starting with '_')"
                            ),
                            hint="add GlyphDraft anchors like {'_top': (0, 0)}",
                        )
                    )

        for comp_name, comp in project.composites.items():
            base = comp.base
            if base not in anchor_names and base not in specs:
                out.append(
                    Finding(
                        check="anchors.composite_base",
                        level="error",
                        glyph=comp_name,
                        master=ctx.master,
                        where=base,
                        measured=None,
                        expected=base,
                        message=f"composite {comp_name!r} base {base!r} is missing",
                        hint="define the base glyph or fix composites.py",
                    )
                )
                continue
            base_anchors = anchor_names.get(base, set())
            for entry in comp.marks:
                if "@" not in entry:
                    out.append(
                        Finding(
                            check="anchors.composite_syntax",
                            level="error",
                            glyph=comp_name,
                            master=ctx.master,
                            where=entry,
                            measured=entry,
                            expected="mark@anchor",
                            message=(
                                f"composite mark entry {entry!r} must be "
                                "'markName@anchorName'"
                            ),
                            hint="example: acutecomb@top",
                        )
                    )
                    continue
                mark_name, anchor = entry.split("@", 1)
                if mark_name not in specs:
                    out.append(
                        Finding(
                            check="anchors.composite_mark",
                            level="error",
                            glyph=comp_name,
                            master=ctx.master,
                            where=mark_name,
                            measured=None,
                            expected=mark_name,
                            message=(
                                f"composite {comp_name!r} mark {mark_name!r} "
                                "is missing"
                            ),
                            hint="add the mark under marks/ or glyphs/",
                        )
                    )
                    continue
                mark_anchors = anchor_names.get(mark_name, set())
                attach = f"_{anchor}"
                if anchor not in base_anchors:
                    out.append(
                        Finding(
                            check="anchors.composite_base_anchor",
                            level="error",
                            glyph=comp_name,
                            master=ctx.master,
                            where=anchor,
                            measured=None,
                            expected=anchor,
                            message=(
                                f"base {base!r} missing anchor {anchor!r} "
                                f"for composite {comp_name!r}"
                            ),
                            hint=f"add GlyphDraft anchors[{anchor!r}] on {base}",
                        )
                    )
                if attach not in mark_anchors:
                    out.append(
                        Finding(
                            check="anchors.composite_mark_anchor",
                            level="error",
                            glyph=comp_name,
                            master=ctx.master,
                            where=attach,
                            measured=None,
                            expected=attach,
                            message=(
                                f"mark {mark_name!r} missing attachment "
                                f"anchor {attach!r} for composite {comp_name!r}"
                            ),
                            hint=f"add GlyphDraft anchors[{attach!r}] on {mark_name}",
                        )
                    )
        return out
