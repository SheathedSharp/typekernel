"""Topology checks: counters, islands, slits, apertures (target §7.2)."""

from __future__ import annotations

from collections.abc import Iterable

from typekernel.anatomy.tags import TagGrammarError, parse_tag
from typekernel.diagnose.protocol import CheckContext, Finding, Scope
from typekernel.perceive.topology import measure_topology
from typekernel.project.manifest import Expect

__all__ = ["TopologyCheck"]


def _expect_for(ctx: CheckContext) -> Expect | None:
    if ctx.name is None:
        return None
    spec = ctx.session.specs().get(ctx.name)
    if spec is not None and spec.expect is not None:
        return spec.expect
    return ctx.project.expect.get(ctx.name)


def _aperture_tags(drawing: object) -> list[str]:
    """Collect aperture.* tags from nodes and slots on a Drawing-like object."""
    tags: list[str] = []
    nodes = getattr(drawing, "nodes", ()) or ()
    for group in nodes:
        for n in group:
            tag = getattr(n, "tag", "")
            if isinstance(tag, str) and tag.startswith("aperture."):
                tags.append(tag)
    slots = getattr(drawing, "slots", ()) or ()
    for slot in slots:
        tag = getattr(slot, "tag", "")
        if isinstance(tag, str) and tag.startswith("aperture."):
            tags.append(tag)
    return tags


def _aperture_index_count(tags: list[str]) -> int:
    """Count unique aperture.N indices (target §7.3 apertures)."""
    indices: set[str] = set()
    for tag in tags:
        try:
            parsed = parse_tag(tag)
        except TagGrammarError:
            indices.add(tag)
            continue
        if parsed.part != "aperture":
            continue
        if parsed.indices:
            indices.add(parsed.indices[0])
        else:
            indices.add(tag)
    return len(indices)


class TopologyCheck:
    id = "topology.counters"
    scope: Scope = "glyph"

    def run(self, ctx: CheckContext) -> Iterable[Finding]:
        if ctx.name is None or ctx.final is None:
            return []
        expect = _expect_for(ctx)
        stem = float(next(iter(ctx.system.stem.values()), 80.0))
        topo = measure_topology(ctx.final.outline(), stem=stem)
        out: list[Finding] = []

        if expect is not None and expect.counters is not None and topo.counters != expect.counters:
                out.append(
                    Finding(
                        check="topology.counters",
                        level="warn",
                        glyph=ctx.name,
                        master=ctx.master,
                        where=None,
                        measured=topo.counters,
                        expected=expect.counters,
                        message=(
                            f"counters={topo.counters} expected {expect.counters}"
                        ),
                        hint="open_bowl / bowl construction; avoid closed ring + bar",
                    )
                )

        if expect is not None and expect.islands is not None and topo.islands != expect.islands:
                out.append(
                    Finding(
                        check="topology.islands",
                        level="warn",
                        glyph=ctx.name,
                        master=ctx.master,
                        where=None,
                        measured=topo.islands,
                        expected=expect.islands,
                        message=(
                            f"islands={topo.islands} expected {expect.islands}"
                        ),
                        hint="check disconnected ink (dots, accents) vs merged shapes",
                    )
                )

        if topo.slit_counters > 0:
            out.append(
                Finding(
                    check="topology.slits",
                    level="warn",
                    glyph=ctx.name,
                    master=ctx.master,
                    where=None,
                    measured=topo.slit_counters,
                    expected=0,
                    message=(
                        f"slit counters={topo.slit_counters} "
                        f"(area < 0.25·stem²); likely overlap join"
                    ),
                    hint="realign bowl/stem overlap or deepen join",
                )
            )

        # Apertures: unique aperture.N indices on raw (pre-fill) tags.
        # open_bowl stamps end slots aperture.N.a/b — count N, not endpoints.
        if expect is not None and expect.apertures is not None:
            drawing = ctx.raw if ctx.raw is not None else ctx.final
            tags = _aperture_tags(drawing)
            counted = _aperture_index_count(tags)
            if counted != expect.apertures:
                out.append(
                    Finding(
                        check="topology.apertures",
                        level="warn",
                        glyph=ctx.name,
                        master=ctx.master,
                        where=",".join(sorted(tags)) or None,
                        measured=counted,
                        expected=expect.apertures,
                        message=(
                            f"aperture indices={counted} expected {expect.apertures}"
                        ),
                        hint="open_bowl should stamp aperture.N.a/b; count unique N",
                    )
                )
        return out
