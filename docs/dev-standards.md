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
- **Never** put ticket slang in the subject (`TK-123`, planner pack ids, private backlog codes).
- Keep bodies short and free of private planner jargon.

Agent-facing short form: [`.agents/skills/typekernel-dev-norms/SKILL.md`](../.agents/skills/typekernel-dev-norms/SKILL.md).

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

Outline changes are not tracked by a golden hash file: `typekernel.qa.outline_hash`
exists so `tk diff` can tell you *which* glyphs a change touched, not to gate
them. List the affected glyphs in the commit message instead.

## Approvals / gates

Human visual or API gates leave a JSON record under `approvals/` (for example
`approvals/geo-public-api.json`). Those files are the durable decision record:
what was approved, by whom, and with what test evidence.

验收与评审：`pytest -q` 跑全部测试；字形质量由视觉审阅决定，不用数值门禁冒充（校样用 `tk proof` 生成，落到本地 `artifacts/`）。公开符号的任何变更都要同步进 [ARCHITECTURE.md](ARCHITECTURE.md) 的交接规格。


## Public repository contents

This repo is meant to read as a normal open-source library. Commit:

- README / VISION / API and recipe docs
- Examples that teach the API (scripts + a few showcase proofs)
- Tests, typed sources, and durable `approvals/*.json` gate records

Do **not** commit:

- Private planner notes, agent trial scratch, or personal briefs
- Regenerable dumps under `artifacts/` (except folder `.gitkeep`s)
- Ticket-named specimen PNGs (`artifacts/tk-*`)
- Local example `out/` binaries beyond the showcase exceptions in `.gitignore`

When adding a new example, ignore its `out/**` by default and un-ignore only the proofs worth showing in the README.
