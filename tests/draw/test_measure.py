"""Drawing.measures — merge / tagged / mirrored_x / signature (P1-5)."""

from __future__ import annotations

from dataclasses import replace

from typekernel.draw import Drawing, Measure, Writer


def _box(
    tag_sw: str,
    tag_ne: str,
    *,
    x0: float = 0.0,
    y0: float = 0.0,
    s: float = 100.0,
) -> Drawing:
    return (
        Writer()
        .start((x0, y0))
        .node(tag_sw)
        .line((x0 + s, y0))
        .line((x0 + s, y0 + s))
        .node(tag_ne)
        .line((x0, y0 + s))
        .close()
        .build()
    )


def _with_measures(drawing: Drawing, *measures: Measure) -> Drawing:
    return replace(drawing, measures=measures)


def test_add_merges_measures_and_tags_resolve() -> None:
    a = _with_measures(
        _box("a_sw", "a_ne", x0=0.0),
        Measure(kind="stem", a="a_sw", b="a_ne", expected=100.0),
    )
    b = _with_measures(
        _box("b_sw", "b_ne", x0=200.0),
        Measure(kind="gap", a="b_sw", b="b_ne"),
    )
    merged = a + b
    assert len(merged.measures) == 2
    assert merged.point(merged.measures[0].a).x == 0.0
    assert merged.point(merged.measures[1].a).x == 200.0
    assert merged.measures[0].kind == "stem"
    assert merged.measures[1].kind == "gap"


def test_tagged_prefixes_measure_labels() -> None:
    d = _with_measures(
        _box("sw", "ne"),
        Measure(kind="height", a="ne"),
        Measure(kind="stem", a="sw", b="ne"),
    )
    tagged = d.tagged("stem")
    assert {n.tag for group in tagged.nodes for n in group} == {"stem.sw", "stem.ne"}
    assert tagged.measures[0] == Measure(kind="height", a="stem.ne")
    assert tagged.measures[1] == Measure(kind="stem", a="stem.sw", b="stem.ne")
    assert tagged.point(tagged.measures[1].a)
    assert tagged.point(tagged.measures[1].b)  # type: ignore[arg-type]


def test_mirrored_x_keeps_measure_semantics() -> None:
    d = _with_measures(
        _box("sw", "ne", x0=10.0, s=80.0),
        Measure(kind="stem", a="sw", b="ne"),
    )
    mirrored = d.mirrored_x(100.0)
    assert mirrored.measures == d.measures
    m = mirrored.measures[0]
    assert m.b is not None
    # Labels still resolve after mirror + contour reverse remapping.
    assert mirrored.point(m.a)
    assert mirrored.point(m.b)


def test_measures_not_in_signature() -> None:
    base = _box("sw", "ne")
    measured = _with_measures(base, Measure(kind="stem", a="sw", b="ne", expected=42.0))
    assert base.signature() == measured.signature()
