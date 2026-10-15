# Development standards

Conventions for contributing to typekernel. Internal task packs and planner
folders stay on the author's machine and are not part of this repository.

## Commit messages

Prefer conventional subjects:

```
feat(geo): add immutable Point value type
test(geo): lock Contour invariants
docs: add development standards
chore: add py.typed and mypy package check
```

Rules:

- Prefer `type(scope): summary` with scopes like `geo`, `optics`, `docs`, or omit scope.
- Subjects describe the human change (“export frozen public API”), not an internal ticket code.
- Keep bodies short and free of private planner jargon.

## Typing

- Ship `src/typekernel/py.typed` so consumers and `mypy -p typekernel` treat the
  package as typed.
- Keep `[tool.setuptools.package-data]` including `py.typed`.
- Run `mypy -p typekernel` in the same pre-merge bar as tests and ruff.
- Third-party stub policy: `fontTools.*` and `pathops` (skia-pathops) may use
  `ignore_missing_imports` in `[tool.mypy.overrides]` until typed stubs exist.
  Do not blanket-ignore the whole world.

## Geometry principles

1. **Cubic is design truth.** Quadratic exists only at the compile boundary
   (`to_quadratic` / `QuadraticContour`).
2. **No default polyline flatten.** Sampling may be derived on demand; it is
   never a canonical contour or export path.
3. **`ConversionReport` must be honest.** Report measured / estimated error and
   the budget; do not invent guarantees fontTools did not provide.
4. **No Shapely / buffer = weight.** Booleans, if any, go through curve-capable
   pathops behind an optional extra — never polygonize-to-boolean for design.
5. **Do not reimplement OpenType.** Tables, TTX, varLib, feaLib, cu2qu stay with
   fontTools (and friends). See [notes/fonttools-reuse.md](notes/fonttools-reuse.md).

## Public API export discipline

- Only symbols listed in a module’s `__all__` (and package re-exports) are
  public. Prefer an explicit short `__all__` over “everything importable”.
- Stable helpers that are not part of the frozen surface stay submodule-only
  (import from `typekernel.geo.contour`, etc.).
- Expanding the frozen surface is a deliberate docs + approval change, not an
  accidental re-export.

## Tests and lint before merge

From a checkout with `pip install -e ".[dev]"`:

```bash
pytest -q
ruff check src tests
mypy -p typekernel
```

All three should be green on the commits you intend to publish.

## Approvals / gates

Human visual or API gates leave a JSON record under `approvals/` (for example
`approvals/geo-public-api.json`). Those files are the durable decision record:
what was approved, by whom, and with what test evidence.

Program exit hooks (before signing pending serif/italic gates): [DEVELOPMENT_PLAN.md](DEVELOPMENT_PLAN.md) §8 — `PYTHONPATH=src python examples/run_m5_program_exit.py` (or `pytest -q tests/docs/test_development_plan_section8.py` plus each gate’s `test_evidence` in `approvals/*.json`). Generate review PNGs/TTFs with `examples/human_review_bundle.py` (does not write `approvals/`). Agent trial protocol: [AGENT_TRIALS.md](AGENT_TRIALS.md) (`snapshot_design.py`, `validate_snapshot.py` on written `snapshot.json`). Never relax `AGENT_SENTENCE` or L3 thresholds to pass a gate.
