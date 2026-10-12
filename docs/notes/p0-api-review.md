# P0 geo-kernel — public API review (GATE-P0-API)

**Status: awaiting human approval.** No `src/` changes are made in this task. The
recorded decision goes in `approvals/GATE-P0-API.json`; that file is deliberately
**not** written yet, because only a human may approve a gate.

Tests at review time: `pytest -q` → **120 passed**; `ruff check src tests` → clean.

## Planned public API

Nothing is exported from `typekernel.geo` yet — `geo/__init__.py` still holds a
docstring only. Re-exporting is P0-026, which is blocked on this gate. The
symbols below are the complete public surface of the submodules today.

| Module | Symbol | Signature |
| --- | --- | --- |
| `point` | `Point` | `(x: float, y: float)`, frozen, slotted, hashable |
| `segment` | `LineSegment` | `(p0, p1)` — both on-curve |
| `segment` | `CubicSegment` | `(p0, p1, p2, p3)` — `p1`, `p2` off-curve |
| `contour` | `Contour` | `(segments: tuple[LineSegment \| CubicSegment, ...], closed: bool = False)` |
| `contour` | `signed_area` | `(contour) -> float` — orientation helper only |
| `outline` | `Outline` | `(contours: tuple[Contour, ...])` |
| `outline` | `bounds` | `(outline) -> tuple[minx, miny, maxx, maxy]` — control-point AABB |
| `path_builder` | `PathBuilder` | `moveTo/lineTo/curveTo/closePath/build` |
| `pens` | `draw_outline` | `(outline, pen: AbstractPen) -> None` |
| `rounding` | `quantize` | `(value, ndigits: int = 3) -> float` |
| `rounding` | `quantize_point` | `(point, ndigits: int = 3) -> Point` |
| `convert_quadratic` | `ConversionReport` | `(max_error, segment_count_in, segment_count_out, budget)` |
| `convert_quadratic` | `QuadraticContour` | `(splines, closed)` — compile-boundary artefact |
| `convert_quadratic` | `to_quadratic` | `(outline, budget: float = 1.0) -> (tuple[QuadraticContour, ...], ConversionReport)` |
| `fixtures` | `load_synthetic_outline` | `(path) -> Outline` |
| `boolean` | `boolean_op` | `(a, b, op: Literal["union","intersection","difference"]) -> Outline` — stub |

Properties: `LineSegment.kind == "line"`, `CubicSegment.kind == "cubic"`,
`*.points -> tuple[Point, ...]`, `Contour.is_empty`, `Outline.contour_count`,
`Outline.iter_segments()`, `QuadraticContour.quadratic_count`,
`Contour.assert_closed_consistent()`.

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

## Decisions this gate should confirm

1. **No shared `Segment` protocol.** `Contour.segments` is typed
   `tuple[LineSegment | CubicSegment, ...]` with the union spelled out inline in
   `contour.py`. The canonical alias arguably belongs in `segment.py`; the task
   files for P0-009/P0-010 allowed only `contour.py`, so it was left inline.
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

## Known limitations / suggested follow-ups

- `bounds`: tight Bézier extrema via `calcCubicBounds` not implemented.
- `to_quadratic`: exact error bound not implemented; sampling only.
- `boolean_op`: no working boolean; curve round-trip from pathops is open.
- `mypy --strict` is configured in `pyproject.toml` but **cannot run**: the
  package has no `py.typed` marker, so mypy reports it cannot type check
  `typekernel`. Unresolved; not in any P0 task's allowed files.
- The `.gitignore` modification adding `.agents/` is uncommitted (pre-existing,
  not made by the agent run).

## On approval

Approval unblocks **P0-026** (re-export the stable symbols from
`geo/__init__.py` with `__all__`), which closes the P0 exit criteria.
