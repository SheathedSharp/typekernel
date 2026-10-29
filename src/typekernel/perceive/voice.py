"""Measurable voice / shape distance between projects (not aesthetic originality).

The kernel does not compute style-consistency or originality scores. This module
only compares structural features an agent can compute: topology, density,
aspect, and normalized advance on a control charset. Subjective distinctiveness
is left to human review.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from typekernel.perceive.explain import explain
from typekernel.perceive.topology import measure_topology
from typekernel.project.session import ProjectSession

__all__ = [
    "CONTROL_GLYPHS",
    "VoiceFeatures",
    "extract_voice",
    "voice_distance",
]

# Control set as Unicode codepoints → AGL names (no glyph-name string literals).
_CONTROL_CODEPOINTS: tuple[int, ...] = (
    0x6E,  # n
    0x6F,  # o
    0x48,  # H
    0x4F,  # O
    0x61,  # a
    0x65,  # e
    0x73,  # s
    0x69,  # i
    0x76,  # v
)


def _control_glyphs() -> tuple[str, ...]:
    from typekernel.font.glyph import glyph_name_for_char

    return tuple(glyph_name_for_char(chr(cp)) for cp in _CONTROL_CODEPOINTS)


CONTROL_GLYPHS: tuple[str, ...] = _control_glyphs()


@dataclass(frozen=True, slots=True)
class VoiceFeatures:
    """Per-glyph feature rows keyed by glyph name."""

    rows: Mapping[str, tuple[float, ...]]
    """(counters, islands, density, aspect, advance/upm) per glyph."""


def extract_voice(
    session: ProjectSession,
    glyphs: Sequence[str] = CONTROL_GLYPHS,
    *,
    master: str | None = None,
) -> VoiceFeatures:
    """Extract comparable features for glyphs present in ``session``."""
    upm = float(session.project.system.upm)
    stem = float(next(iter(session.project.system.stem.values()), 80.0))
    rows: dict[str, tuple[float, ...]] = {}
    specs = session.specs()
    for name in glyphs:
        if name not in specs:
            continue
        try:
            report = explain(session, name, master=master)
            draft = session.evaluate(name, master=master)
        except (KeyError, ValueError, TypeError, RuntimeError):
            continue
        topo = measure_topology(draft.drawing.outline(), stem=stem)
        bx0, by0, bx1, by1 = report.bbox
        aspect = (by1 - by0) / max(bx1 - bx0, 1e-6)
        adv = float(session.glyph(name, master=master).advance) / upm
        rows[name] = (
            float(topo.counters),
            float(topo.islands),
            float(report.ink_density),
            float(aspect),
            adv,
        )
    return VoiceFeatures(rows=rows)


def voice_distance(a: VoiceFeatures, b: VoiceFeatures) -> float:
    """L2 distance on shared glyphs (0 = identical feature rows).

    Missing glyphs on either side are skipped. Empty overlap → ``inf``.
    """
    shared = sorted(set(a.rows) & set(b.rows))
    if not shared:
        return float("inf")
    total = 0.0
    for name in shared:
        ra, rb = a.rows[name], b.rows[name]
        if len(ra) != len(rb):
            continue
        for x, y in zip(ra, rb, strict=True):
            d = float(x) - float(y)
            total += d * d
    return float(total**0.5)
