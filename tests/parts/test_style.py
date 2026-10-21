"""TK-305 Style DNA (scaffold + i_dot)."""

from __future__ import annotations

from typekernel.parts import DesignContext, FormSources
from typekernel.parts.style import Style
from typekernel.qa.originality import nearest_voice_distance, topology_signature
from typekernel.qa.outline_hash import composed_glyph_hash


def test_default_style_preserves_preset_i_hash() -> None:
    for preset in ("humanist_sans", "geometric_sans", "code_clear"):
        ctx = getattr(DesignContext, preset)()
        base = FormSources.from_context(ctx).derive("i")["i"]
        again = FormSources.from_context(ctx, style=Style()).derive("i")["i"]
        assert composed_glyph_hash(base) == composed_glyph_hash(again)


def test_i_dot_square_changes_topology() -> None:
    ctx = DesignContext.geometric_sans()
    round_i = FormSources.from_context(ctx).derive("i")["i"]
    square_i = FormSources.from_context(ctx, style=Style(i_dot="square")).derive("i")["i"]
    assert topology_signature(round_i) != topology_signature(square_i)


def test_with_style_helper() -> None:
    controls = FormSources.from_context(DesignContext.humanist_sans()).with_style(i_dot="diamond")
    assert controls.style.i_dot == "diamond"
    assert controls.context.style.i_dot == "diamond"


def test_non_default_style_raises_voice_distance() -> None:
    base = FormSources.from_context(DesignContext.humanist_sans())
    styled = base.with_style(i_dot="diamond")
    assert nearest_voice_distance(styled) > nearest_voice_distance(base)


def test_a_form_double_changes_topology_and_voice() -> None:
    ctx = DesignContext.geometric_sans()
    single = FormSources.from_context(ctx).derive("a")["a"]
    double = FormSources.from_context(ctx, style=Style(a_form="double")).derive("a")["a"]
    assert topology_signature(single) != topology_signature(double)
    base_dist = nearest_voice_distance(FormSources.from_context(ctx))
    double_dist = nearest_voice_distance(FormSources.from_context(ctx, style=Style(a_form="double")))
    assert double_dist > base_dist


def test_a_form_double_lint_clean_on_geometric() -> None:
    controls = FormSources.from_context(DesignContext.geometric_sans(), style=Style(a_form="double"))
    from typekernel.qa.lint import lint_glyph

    issues = lint_glyph(controls.derive("a")["a"], controls.context, glyph_name="a")
    assert not [i for i in issues if i.severity == "error"]


def test_l_tail_tailed_changes_topology() -> None:
    ctx = DesignContext.geometric_sans()
    plain = FormSources.from_context(ctx).derive("l")["l"]
    tailed = FormSources.from_context(ctx, style=Style(l_tail="tailed")).derive("l")["l"]
    assert topology_signature(plain) != topology_signature(tailed)


def test_y_tail_curved_changes_outline() -> None:
    ctx = DesignContext.geometric_sans()
    straight = FormSources.from_context(ctx).derive("y")["y"]
    curved = FormSources.from_context(ctx, style=Style(y_tail="curved")).derive("y")["y"]
    assert composed_glyph_hash(straight) != composed_glyph_hash(curved)


def test_g_form_double_changes_topology() -> None:
    ctx = DesignContext.geometric_sans()
    single = FormSources.from_context(ctx).derive("g")["g"]
    double = FormSources.from_context(ctx, style=Style(g_form="double")).derive("g")["g"]
    assert topology_signature(single) != topology_signature(double)


def test_t_cut_slanted_changes_outline_on_vertical_terminal() -> None:
    ctx = DesignContext.geometric_sans().tuned(terminal_style="vertical")
    flat = FormSources.from_context(ctx).derive("t")["t"]
    slant = FormSources.from_context(ctx, style=Style(t_cut="slanted")).derive("t")["t"]
    assert composed_glyph_hash(flat) != composed_glyph_hash(slant)


def test_t_cut_flat_matches_default_on_preset() -> None:
    ctx = DesignContext.humanist_sans()
    a = composed_glyph_hash(FormSources.from_context(ctx).derive("t")["t"])
    b = composed_glyph_hash(FormSources.from_context(ctx, style=Style(t_cut="flat")).derive("t")["t"])
    assert a == b


def test_g_form_double_lint_clean_on_geometric() -> None:
    controls = FormSources.from_context(DesignContext.geometric_sans(), style=Style(g_form="double"))
    from typekernel.qa.lint import lint_glyph

    issues = lint_glyph(controls.derive("g")["g"], controls.context, glyph_name="g")
    assert not [i for i in issues if i.severity == "error"]
