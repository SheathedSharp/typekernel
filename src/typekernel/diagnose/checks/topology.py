"""B-class topology: counters, islands, slits, apertures (target §7.2)."""

from __future__ import annotations

from collections.abc import Iterable

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

        # Apertures: count aperture.* tags when expect.apertures is set.
        if expect is not None and expect.apertures is not None:
            tags = [
                n.tag
                for group in ctx.final.nodes
                for n in group
                if n.tag.startswith("aperture.")
            ]
            counted = len(tags)
            if counted != expect.apertures:
                out.append(
                    Finding(
                        check="topology.apertures",
                        level="warn",
                        glyph=ctx.name,
                        master=ctx.master,
                        where=",".join(tags) or None,
                        measured=counted,
                        expected=expect.apertures,
                        message=(
                            f"aperture tags={counted} expected {expect.apertures}"
                        ),
                        hint="open_bowl should stamp aperture.* tags",
                    )
                )
        return out
