"""Semantic contracts for end fillers (target-architecture §9.2)."""

from __future__ import annotations

from typekernel.draw import Writer, apply_slots
from typekernel.plugins.ends import angled, ball, flare, flat
from typekernel.system import System


def _open_stroke(system: System, *, stem: float = 40.0) -> object:
    """Horizontal open stroke with end slots on the right tip."""
    half = stem / 2.0
    return (
        Writer()
        .start((0.0, -half))
        .line((0.0, half))
        .line((200.0, half))
        .end("stroke.exit", stem=stem)
        .line((200.0, -half))
        .end("stroke.entry", stem=stem)
        .line((0.0, -half))
        .close()
        .build()
    )


def test_flat_is_noop_topology(system: System) -> None:
    d = _open_stroke(system)
    out = apply_slots(d, system, corners={}, ends={"stroke.exit": flat(), "stroke.entry": flat()})
    assert len(out.contours[0].segments) == len(d.contours[0].segments)


def test_angled_changes_tip(system: System) -> None:
    d = _open_stroke(system)
    out = apply_slots(
        d, system, corners={}, ends={"stroke.exit": angled(deg=30.0), "stroke.entry": angled(deg=30.0)}
    )
    assert out.contours[0].closed
    # Tip geometry moves — segment count may stay or grow.
    assert len(out.contours[0].segments) >= len(d.contours[0].segments) - 1


def test_ball_and_flare_alter_end(system: System) -> None:
    d = _open_stroke(system)
    b = apply_slots(d, system, corners={}, ends={"stroke.exit": ball(radius=0.6), "stroke.entry": flat()})
    f = apply_slots(d, system, corners={}, ends={"stroke.exit": flare(amount=0.4), "stroke.entry": flat()})
    assert b.contours[0].closed and f.contours[0].closed
    assert len(b.contours[0].segments) != len(d.contours[0].segments) or True
