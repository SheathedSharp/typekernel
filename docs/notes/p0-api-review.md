# Geo-kernel — public API review

**Status: approved.** Decision recorded in [`approvals/GATE-P0-API.json`](../../approvals/GATE-P0-API.json)
(filename kept as a stable gate artifact; see [docs/dev-standards.md](../dev-standards.md)).

Tests at review / approval time: `pytest -q` → **120 passed**; `ruff check src tests` → clean.
Hygiene follow-ups since approval add `py.typed`, mypy package check, and segment
continuity validation (re-run the suite after those land).

## Public API

Stable symbols are re-exported from `typekernel.geo` (see `geo/__init__.py` and
`__all__`). Helpers that stay submodule-only must be imported from their home
module.

### Re-exported from `typekernel.geo`

| Symbol | Home module | Signature / notes |
| --- | --- | --- |
| `Point` | `point` | `(x: float, y: float)`, frozen, slotted, hashable |
| `LineSegment` | `segment` | `(p0, p1)` — both on-curve |
| `CubicSegment` | `segment` | `(p0, p1, p2, p3)` — `p1`, `p2` off-curve |
| `Contour` | `contour` | `(segments: tuple[LineSegment \| CubicSegment, ...], closed: bool = False)` |
| `Outline` | `outline` | `(contours: tuple[Contour, ...])` |
| `PathBuilder` | `path_builder` | `moveTo` / `lineTo` / `curveTo` / `closePath` / `build` |
| `draw_outline` | `pens` | `(outline, pen: AbstractPen) -> None` |
| `ConversionReport` | `convert_quadratic` | `(max_error, segment_count_in, segment_count_out, budget)` |
| `to_quadratic` | `convert_quadratic` | `(outline, budget: float = 1.0) -> (tuple[QuadraticContour, ...], ConversionReport)` |

### Stable but submodule-only

| Module | Symbol | Signature / notes |
| --- | --- | --- |
| `contour` | `signed_area` | `(contour) -> float` — orientation helper only |
| `contour` | `Contour.assert_closed_consistent` | closed start/end exact match |
| `contour` | `Contour.assert_segments_continuous` | adjacent end→start exact match |
| `outline` | `bounds` | `(outline) -> tuple[minx, miny, maxx, maxy]` — control-point AABB |
| `rounding` | `quantize` | `(value, ndigits: int = 3) -> float` |
| `rounding` | `quantize_point` | `(point, ndigits: int = 3) -> Point` |
| `convert_quadratic` | `QuadraticContour` | `(splines, closed)` — compile-boundary artefact |
| `fixtures` | `load_synthetic_outline` | `(path) -> Outline` |
| `boolean` | `boolean_op` | `(a, b, op) -> Outline` — stub |

Properties: `LineSegment.kind == "line"`, `CubicSegment.kind == "cubic"`,
`*.points -> tuple[Point, ...]`, `Contour.is_empty`, `Outline.contour_count`,
`Outline.iter_segments()`, `QuadraticContour.quadratic_count`.

## The cubic-first story, as enforced in code

1. **There is no quadratic design type.** Quadratics appear only as
   `QuadraticContour`, a compile-boundary value that deliberately does not reuse
   `Contour`/`CubicSegment`, so it cannot be mistaken for design truth.
2. **There is no polyline type, and no flatten entry point.**
   `tests/geo/test_no_polyline_default.py` fails if any `geo` module exposes
   `flatten`/`to_polyline`/`as_polyline`/`sample_polyline`/`polyline`, and parses
   `pens.py`'s AST to prove the export path cannot call a sampler or pass
   `steps=`.
3. **Rounding is opt-in.** `PathBuilder` returns coordinates verbatim; a test
   asserts that. `quantize` is documented as Python `round` (half-to-even) and
   explicitly *not* suitable for font units, where `otRound` (half-away-from-zero)
   is required — the trap is pinned by a test.
4. **Math is delegated.** `fontTools.misc.bezierTools` / `cu2qu` / `AreaPen` /
   `BoundsPen` do the work; the kernel adds typed values, not new mathematics.

## Decisions confirmed at the gate

1. **No shared `Segment` protocol.** `Contour.segments` is typed
   `tuple[LineSegment | CubicSegment, ...]` with the union spelled out inline in
   `contour.py`.
2. **`closePath()` appends an explicit closing line segment** when the current
   point differs from the contour start. Without it, every builder-made closed
   contour would fail `Contour.assert_closed_consistent()`. This makes
   `moveTo/lineTo/lineTo/closePath` produce a **3-segment** triangle, not 2.
3. **Open paths are kept, not rejected.** `build()` includes an unfinished
   contour as an open `Contour`. Contours with no segments are dropped.
4. **`build()` is non-destructive** — it snapshots and does not reset state.
5. **`signed_area` is a shoelace pass over on-curve points only.** Sign is
   reliable (verified against `AreaPen` on the fixture); magnitude is *not* the
   enclosed area and must not be reported as one.
6. **`bounds` is the control-point AABB**, so it contains the shape but is not
   tight. `BoundsPen` is the escape hatch.
7. **Degenerate segments (`p0 == p1`) are tolerated, not rejected.**
8. **`to_quadratic` reports `max_error` measured by sampling** (1000 samples per
   cubic, equal parameter). `fontTools.cu2qu` takes the budget as *input* and
   never reports achieved error, so the number is ours: a deterministic estimate,
   not a proof. The budget remains the hard guarantee.
9. **`boolean_op` is a stub** that raises `RuntimeError` (no pathops) or
   `NotImplementedError` (curve round-trip unresolved). Shapely is never used.

## Known limitations / follow-ups

- `bounds`: tight Bézier extrema via `calcCubicBounds` not implemented.
- `to_quadratic`: exact error bound not implemented; sampling only.
- `boolean_op`: no working boolean; curve round-trip from pathops is open.
- Typed package: `py.typed` + mypy package check are hygiene follow-ups (third-party
  stubs for `fontTools.*` / `pathops` may still need `ignore_missing_imports`).

## After approval

The geo public API is exported from `typekernel.geo` with an explicit `__all__`.
That closes the geo-kernel exit criteria for the public surface; optical /
design-semantics work builds on top of it.
