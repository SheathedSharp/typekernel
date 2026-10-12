# Development standards

Human-facing conventions for typekernel. Internal planner folders and task IDs
(`.agents/`, codes like `P0-026`) are **not** the voice of the product — they
stay local and must not leak into commit subjects or user-facing prose.

## What belongs in git vs local only

| In the repo | Local only (gitignored) |
| --- | --- |
| `src/`, `tests/`, `docs/`, `approvals/`, `pyproject.toml`, … | `.agents/` — agent micro-tasks, phase checklists, session prompts |
| Gate decision JSON under `approvals/` (stable artifacts) | Scratch notes, private plans, unshared foundation docs |

`.agents/` is ignored so weak-model task packs never land on GitHub. If you need
a principle documented for humans, put it here under `docs/`, not only in a
planner task file.

## Commit messages

Use conventional-ish subjects:

```
feat(geo): add immutable Point value type
test(geo): lock Contour invariants
docs: add development standards
chore: add py.typed and mypy package check
```

Rules:

- Prefer `type(scope): summary` with scopes like `geo`, `docs`, or omit scope.
- **Never** put internal planner IDs in subjects or bodies: no `P0-026`,
  `P1-003`, `GATE-P0-API` as slang in every commit.
- Gates and approvals may be **named in docs and `approvals/` files**. The
  approval artifact `approvals/GATE-P0-API.json` keeps that filename for
  stability; in prose prefer “geo public API gate” and link the file once.
- Subjects describe the human change (“export frozen public API”), not the
  ticket number that scheduled it.

## Phase names in human docs

| Prefer in docs / README | Optional internal planner folders |
| --- | --- |
| geo kernel / geo-kernel | `.agents/phases/P0-geo-kernel/` |
| optical primitives | `.agents/phases/P1-optical-primitives/` |
| masters / designspace | `.agents/phases/P2-masters-designspace/` |
| compile bridge | `.agents/phases/P3-compile-bridge/` |

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

Human visual or API gates leave a JSON record under `approvals/`. Those files
are the durable decision; planner task codes that scheduled the gate are not
required in every commit message. Explain the filename once when introducing a
new gate artifact; thereafter link it.
