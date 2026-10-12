"""Guard tests: flattening is never a default design path.

These tests exist to fail loudly if someone later makes a polyline the canonical
outline, or wires a sampler into the export path. Sampling is allowed only as an
explicitly named debug aid that nothing calls on the way out.
"""

import ast
import importlib
import pkgutil
from pathlib import Path

from fontTools.pens.recordingPen import RecordingPen

import typekernel.geo
from typekernel.geo.contour import Contour
from typekernel.geo.outline import Outline
from typekernel.geo.path_builder import PathBuilder
from typekernel.geo.pens import draw_outline
from typekernel.geo.point import Point
from typekernel.geo.segment import CubicSegment

FORBIDDEN_PUBLIC_NAMES = frozenset(
    {"flatten", "to_polyline", "as_polyline", "sample_polyline", "polyline"}
)

GEO_SOURCE = Path(typekernel.geo.__file__).parent


def _geo_modules() -> list[object]:
    modules = [typekernel.geo]
    for info in pkgutil.iter_modules([str(GEO_SOURCE)]):
        modules.append(importlib.import_module(f"typekernel.geo.{info.name}"))
    return modules


def test_no_geo_module_exposes_a_flattening_api() -> None:
    """A public flatten/sample entry point would be a design-truth leak."""
    offenders = {
        module.__name__: sorted(FORBIDDEN_PUBLIC_NAMES.intersection(dir(module)))
        for module in _geo_modules()
        if FORBIDDEN_PUBLIC_NAMES.intersection(dir(module))
    }
    assert offenders == {}


def test_cubic_contours_reach_the_pen_as_curves() -> None:
    builder = PathBuilder()
    builder.moveTo(0.0, 0.0)
    # Return to the start so closePath has no closing line to add.
    builder.curveTo(0.0, 10.0, 10.0, 10.0, 0.0, 0.0)
    builder.closePath()
    pen = RecordingPen()
    draw_outline(builder.build(), pen)
    ops = [op for op, _ in pen.value]
    assert "curveTo" in ops
    assert "lineTo" not in ops


def test_pens_module_does_not_reference_any_sampler() -> None:
    """The export path must not be able to flatten, even accidentally.

    Checked structurally via the AST rather than by substring: the module's
    prose legitimately contains the word "flattening" while promising not to.
    """
    tree = ast.parse((GEO_SOURCE / "pens.py").read_text(encoding="utf-8"))
    identifiers = {node.id for node in ast.walk(tree) if isinstance(node, ast.Name)}
    attributes = {node.attr for node in ast.walk(tree) if isinstance(node, ast.Attribute)}
    keywords = {
        keyword.arg
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        for keyword in node.keywords
    }
    assert not (identifiers | attributes).intersection(FORBIDDEN_PUBLIC_NAMES)
    assert "steps" not in keywords


def test_path_builder_documents_that_it_never_flattens() -> None:
    docstring = PathBuilder.__module__ and importlib.import_module(
        "typekernel.geo.path_builder"
    ).__doc__
    assert docstring is not None
    assert "no flattening or sampling entry point" in docstring


def test_curve_data_survives_a_builder_round_trip_intact() -> None:
    """The builder must not quietly replace handles with sampled points."""
    builder = PathBuilder()
    builder.moveTo(0.0, 0.0)
    builder.curveTo(1.0, 2.0, 3.0, 4.0, 5.0, 6.0)
    segment = builder.build().contours[0].segments[0]
    assert segment == CubicSegment(
        Point(0.0, 0.0), Point(1.0, 2.0), Point(3.0, 4.0), Point(5.0, 6.0)
    )


def test_outline_holds_segments_not_vertex_lists() -> None:
    """The canonical contour data must be segment objects, never raw points."""
    outline = Outline((Contour((CubicSegment(Point(0, 0), Point(1, 1), Point(2, 2), Point(3, 3)),), closed=False),))
    segment = outline.contours[0].segments[0]
    assert not isinstance(segment, tuple)
    assert not isinstance(segment, list)
    assert segment.kind == "cubic"
