"""Suffix → feature codegen (§11.1)."""

from __future__ import annotations

from typekernel.features import assemble_features, generate_features, parse_suffix, validate_fea


def test_parse_suffix_variants() -> None:
    assert parse_suffix("a.ss01") == ("sub", "ss01", "a")
    assert parse_suffix("A.sc") == ("sub", "c2sc", "A")
    assert parse_suffix("a.sc") == ("sub", "smcp", "a")
    assert parse_suffix("zero.tf") == ("sub", "tnum", "zero")
    assert parse_suffix("zero.osf") == ("sub", "onum", "zero")
    assert parse_suffix("period.case") == ("sub", "case", "period")
    assert parse_suffix("f_i") == ("liga", "liga", "f_i")


def test_generate_emits_ss01_tnum_onum_case() -> None:
    text = generate_features(
        {"a", "a.ss01", "zero", "zero.tf", "zero.osf", "period", "period.case"}
    )
    assert "feature ss01" in text and "sub a by a.ss01" in text
    assert "feature tnum" in text and "sub zero by zero.tf" in text
    assert "feature onum" in text and "sub zero by zero.osf" in text
    assert "feature case" in text and "sub period by period.case" in text
    validate_fea(text)


def test_tk_replace_drops_auto_feature(tmp_path) -> None:
    fea = tmp_path / "features"
    fea.mkdir()
    (fea / "ss01.fea").write_text(
        "# tk:replace ss01\nfeature ss01 {\n  sub a by a.ss01;\n} ss01;\n",
        encoding="utf-8",
    )
    text = assemble_features(
        {"a", "a.ss01"},
        fea_dir="features",
        root=tmp_path,
    )
    # Auto ss01 stripped; hand file present once
    assert text.count("feature ss01") == 1
    assert "tk:replace" in text or "ss01.fea" in text
    validate_fea(text)
