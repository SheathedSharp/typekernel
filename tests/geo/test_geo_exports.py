"""Unit tests for the geo public API frozen by approvals/geo-public-api.json."""

import importlib

import typekernel.geo

EXPECTED_EXPORTS = frozenset(
    {
        "Contour",
        "ConversionReport",
        "CubicSegment",
        "LineSegment",
        "Outline",
        "PathBuilder",
        "Point",
        "draw_outline",
        "to_quadratic",
    }
)

ORIGINS = {
    "Point": ("typekernel.geo.point", "Point"),
    "LineSegment": ("typekernel.geo.segment", "LineSegment"),
    "CubicSegment": ("typekernel.geo.segment", "CubicSegment"),
    "Contour": ("typekernel.geo.contour", "Contour"),
    "Outline": ("typekernel.geo.outline", "Outline"),
    "PathBuilder": ("typekernel.geo.path_builder", "PathBuilder"),
    "draw_outline": ("typekernel.geo.pens", "draw_outline"),
    "to_quadratic": ("typekernel.geo.convert_quadratic", "to_quadratic"),
    "ConversionReport": ("typekernel.geo.convert_quadratic", "ConversionReport"),
}

SECONDARY_HELPERS = (
    "signed_area",
    "bounds",
    "quantize",
    "quantize_point",
    "QuadraticContour",
    "load_synthetic_outline",
    "boolean_op",
)


def test_all_matches_the_frozen_api() -> None:
    assert set(typekernel.geo.__all__) == EXPECTED_EXPORTS


def test_every_exported_name_resolves() -> None:
    for name in typekernel.geo.__all__:
        assert hasattr(typekernel.geo, name), name


def test_exports_are_the_same_objects_as_their_submodules() -> None:
    """Re-exporting must alias, not copy or re-wrap."""
    for name, (module_name, attribute) in ORIGINS.items():
        module = importlib.import_module(module_name)
        assert getattr(typekernel.geo, name) is getattr(module, attribute)


def test_no_private_helpers_are_exported() -> None:
    assert not [name for name in typekernel.geo.__all__ if name.startswith("_")]


def test_optics_is_not_exported() -> None:
    assert not [name for name in typekernel.geo.__all__ if "optic" in name.lower()]
    assert not hasattr(typekernel.geo, "optics")


def test_secondary_helpers_stay_in_their_submodules() -> None:
    """Deliberate: the top level is a short list, not everything public."""
    for name in SECONDARY_HELPERS:
        assert name not in typekernel.geo.__all__
        assert not hasattr(typekernel.geo, name), f"{name} leaked to the top level"


def test_star_import_exports_exactly_all() -> None:
    namespace: dict[str, object] = {}
    exec("from typekernel.geo import *", namespace)  # noqa: S102
    exported = {name for name in namespace if not name.startswith("__")}
    assert exported == EXPECTED_EXPORTS


def test_the_documented_top_level_import_works() -> None:
    from typekernel.geo import Outline, PathBuilder, Point

    assert Point is typekernel.geo.Point
    assert Outline is typekernel.geo.Outline
    assert PathBuilder is typekernel.geo.PathBuilder


def test_the_cubic_first_story_is_reachable_from_the_top_level() -> None:
    """A caller can build cubics and convert them without touching submodules."""
    from typekernel.geo import ConversionReport, CubicSegment, Outline, PathBuilder, Point

    builder = PathBuilder()
    builder.moveTo(0.0, 0.0)
    builder.curveTo(0.0, 10.0, 10.0, 10.0, 0.0, 0.0)
    builder.closePath()
    outline = builder.build()
    assert outline.contour_count == 1
    assert isinstance(outline.contours[0].segments[0], CubicSegment)
    assert Point(0.0, 0.0) in outline.contours[0].segments[0].points
    assert isinstance(Outline(()).contour_count, int)
    assert ConversionReport.__name__ == "ConversionReport"
