"""M1 exit sample: synthetic stem + arch + stem (ARCHITECTURE.md §9.9 / §9.10 #9)."""

from __future__ import annotations

from pathlib import Path

from typekernel.draw import Writer, tensioned_arc
from typekernel.geo.contour import signed_area
from typekernel.geo.point import Point
from typekernel.geo.smoothness import g1_join_error


def arch_body(
    *,
    left_x: float = 0.0,
    right_x: float = 100.0,
    baseline: float = 0.0,
    x_height: float = 100.0,
    tension: float = 0.55,
):
    """Outer ink: left stem → raised arch → right stem → baseline.

    Synthetic geometry only — not a letter. ≤ 40 lines of Writer program.
    Stem tops are declared corners; the arch itself is G1 end-to-end.
    """
    # --- Writer program (≤ 40 lines) ---
    top, bot = x_height, baseline
    # Raised arch: upward-ish leave, downward-ish arrive (same end heights).
    arch = tensioned_arc(
        (left_x, top),
        (1.0, 0.8),
        (right_x, top),
        (1.0, -0.8),
        tension=tension,
    )
    return (
        Writer()
        .start((left_x, bot))
        .node("stem.l.foot")
        .line((left_x, top))
        .corner("stem.l.top")
        .fragment(arch, prefix="arch")
        .corner("stem.r.top")
        .line((right_x, bot))
        .node("stem.r.foot")
        .line((left_x, bot))
        .close()
        .build()
    )
    # --- end Writer program ---


def test_arch_body_single_contour_ccw_corners_or_g1() -> None:
    d = arch_body()
    assert len(d.contours) == 1
    assert d.roles == ("ink",)
    assert signed_area(d.contours[0]) > 0
    assert d.point("stem.l.foot") == Point(0.0, 0.0)
    assert d.point("stem.r.foot") == Point(100.0, 0.0)
    assert d.point("stem.l.top") == Point(0.0, 100.0)
    assert d.point("stem.r.top") == Point(100.0, 100.0)
    corner_tags = {s.tag for s in d.slots if s.kind == "corner"}
    assert corner_tags == {"stem.l.top", "stem.r.top"}
    # Joins at non-corner nodes: if a curve is involved, must be G1.
    # Node i is the start of segment i (join between segs[i-1] and segs[i]).
    segs = d.contours[0].segments
    n = len(segs)
    corner_nodes = {s.node for s in d.slots if s.kind == "corner"}
    for i in range(n):
        if i in corner_nodes:
            continue
        a, b = segs[(i - 1) % n], segs[i]
        if a.kind == "cubic" or b.kind == "cubic":
            assert g1_join_error(a, b) < 1e-6
    arch_seg = next(s for s in segs if s.kind == "cubic")
    assert max(arch_seg.p1.y, arch_seg.p2.y) > 100.0


def test_arch_body_writer_program_within_40_lines() -> None:
    src = Path(__file__).read_text(encoding="utf-8")
    start = src.index("# --- Writer program")
    end = src.index("# --- end Writer program")
    line_count = src[start:end].count("\n")
    assert line_count <= 40, f"arch_body Writer program is {line_count} lines (limit 40)"
