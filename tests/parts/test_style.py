"""TK-305 Style DNA (scaffold + i_dot)."""

from __future__ import annotations

from typekernel.parts import Controls, DesignContext
from typekernel.parts.style import Style
from typekernel.qa.originality import nearest_voice_distance, topology_signature
from typekernel.qa.outline_hash import composed_glyph_hash


def test_default_style_preserves_preset_i_hash() -> None:
    for preset in ("humanist_sans", "geometric_sans", "code_clear"):
        ctx = getattr(DesignContext, preset)()
        base = Controls.from_context(ctx).build_all("i")["i"]
        again = Controls.from_context(ctx, style=Style()).build_all("i")["i"]
        assert composed_glyph_hash(base) == composed_glyph_hash(again)


def test_i_dot_square_changes_topology() -> None:
    ctx = DesignContext.geometric_sans()
    round_i = Controls.from_context(ctx).build_all("i")["i"]
    square_i = Controls.from_context(ctx, style=Style(i_dot="square")).build_all("i")["i"]
    assert topology_signature(round_i) != topology_signature(square_i)


def test_with_style_helper() -> None:
    controls = Controls.from_context(DesignContext.humanist_sans()).with_style(i_dot="diamond")
    assert controls.style.i_dot == "diamond"
    assert controls.context.style.i_dot == "diamond"


def test_non_default_style_raises_voice_distance() -> None:
    base = Controls.from_context(DesignContext.humanist_sans())
    styled = base.with_style(i_dot="diamond")
    assert nearest_voice_distance(styled) > nearest_voice_distance(base)


def test_a_form_double_changes_topology_and_voice() -> None:
    ctx = DesignContext.geometric_sans()
    single = Controls.from_context(ctx).build_all("a")["a"]
    double = Controls.from_context(ctx, style=Style(a_form="double")).build_all("a")["a"]
    assert topology_signature(single) != topology_signature(double)
    base_dist = nearest_voice_distance(Controls.from_context(ctx))
    double_dist = nearest_voice_distance(Controls.from_context(ctx, style=Style(a_form="double")))
    assert double_dist > base_dist


def test_a_form_double_lint_clean_on_geometric() -> None:
    controls = Controls.from_context(DesignContext.geometric_sans(), style=Style(a_form="double"))
    from typekernel.qa.lint import lint_glyph

    issues = lint_glyph(controls.build_all("a")["a"], controls.context, glyph_name="a")
    assert not [i for i in issues if i.severity == "error"]


def test_l_tail_tailed_changes_topology() -> None:
    ctx = DesignContext.geometric_sans()
    plain = Controls.from_context(ctx).build_all("l")["l"]
    tailed = Controls.from_context(ctx, style=Style(l_tail="tailed")).build_all("l")["l"]
    assert topology_signature(plain) != topology_signature(tailed)


def test_y_tail_curved_changes_outline() -> None:
    ctx = DesignContext.geometric_sans()
    straight = Controls.from_context(ctx).build_all("y")["y"]
    curved = Controls.from_context(ctx, style=Style(y_tail="curved")).build_all("y")["y"]
    assert composed_glyph_hash(straight) != composed_glyph_hash(curved)


def test_g_form_double_changes_topology() -> None:
    ctx = DesignContext.geometric_sans()
    single = Controls.from_context(ctx).build_all("g")["g"]
    double = Controls.from_context(ctx, style=Style(g_form="double")).build_all("g")["g"]
    assert topology_signature(single) != topology_signature(double)


def test_t_cut_slanted_changes_outline_on_vertical_terminal() -> None:
    ctx = DesignContext.geometric_sans().tuned(terminal_style="vertical")
    flat = Controls.from_context(ctx).build_all("t")["t"]
    slant = Controls.from_context(ctx, style=Style(t_cut="slanted")).build_all("t")["t"]
    assert composed_glyph_hash(flat) != composed_glyph_hash(slant)


def test_t_cut_flat_matches_default_on_preset() -> None:
    ctx = DesignContext.humanist_sans()
    a = composed_glyph_hash(Controls.from_context(ctx).build_all("t")["t"])
    b = composed_glyph_hash(Controls.from_context(ctx, style=Style(t_cut="flat")).build_all("t")["t"])
    assert a == b


def test_g_form_double_lint_clean_on_geometric() -> None:
    controls = Controls.from_context(DesignContext.geometric_sans(), style=Style(g_form="double"))
    from typekernel.qa.lint import lint_glyph

    issues = lint_glyph(controls.build_all("g")["g"], controls.context, glyph_name="g")
    assert not [i for i in issues if i.severity == "error"]
