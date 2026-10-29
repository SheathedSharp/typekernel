"""Combining below marks for latin-sans — cedilla / ogonek."""

from __future__ import annotations

from typekernel.anatomy import drop, hook
from typekernel.project import GlyphDraft, glyph
from typekernel.system import System


def _st(system: System) -> float:
    return float(system.stem["lc"])


@glyph("cedillacomb", unicodes=(0x0327,), group="marks", traits=("mark",))
def cedillacomb(system: System):
    st = _st(system) * 0.55
    # Attachment at origin (base bottom); ink hangs below.
    body = drop((0.0, -st * 0.1), (0.0, -st * 2.4), width=st * 1.1, name="drop")
    return GlyphDraft(drawing=body, anchors={"_bottom": (0.0, 0.0)})


@glyph("ogonekcomb", unicodes=(0x0328,), group="marks", traits=("mark",))
def ogonekcomb(system: System):
    st = _st(system) * 0.5
    # Hook curling right/down from attachment.
    body = hook(
        0.0,
        0.0,
        (st * 1.6, -st * 2.0),
        thick=st,
        thin=st * 0.75,
        depth=st * 1.2,
        name="hook",
    )
    return GlyphDraft(drawing=body, anchors={"_ogonek": (0.0, 0.0), "_bottom": (0.0, 0.0)})
