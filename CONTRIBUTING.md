# Contributing

Thanks for looking at typekernel. This file is the short version; the long-form
rules live in [docs/dev-standards.md](docs/dev-standards.md).

## Setup

```bash
git clone https://github.com/SheathedSharp/typekernel
cd typekernel
python -m venv .venv && . .venv/bin/activate
pip install -e ".[dev,specimen,compile]"
```

`dev` gives you pytest / ruff / mypy; `specimen` adds Pillow for proof PNGs;
`compile` adds ufoLib2 / fontmake / ufo2ft for OTF / TTF / VF output.

## Before you open a PR

All three should be green:

```bash
pytest -q
ruff check src tests
mypy -p typekernel
```

If your change touches outlines, say which glyphs moved in the commit message.
There is no golden-hash gate — `typekernel.qa.outline_hash` exists so `tk diff`
can report what changed, not to freeze it.

## Commit messages

Conventional commits, Chinese or English subject, one theme per commit:

```
feat(draw): Writer 支持在角点声明槽位
fix(geo): 修正 mirrored_x 的节点 index 重映射
docs: 说明 tk audit 的 stem 偏差怎么读
```

`scope` should match the tree you touched (`geo`, `draw`, `optics`, `compile`,
`starters`, `cli`, `docs`, `ci`). Subjects describe the human change — never an
internal ticket code or planner id. Machine-readable short form:
[`.agents/skills/typekernel-dev-norms/SKILL.md`](.agents/skills/typekernel-dev-norms/SKILL.md).

## What belongs in the repo

Commit: sources and tests, the docs listed in the README, examples that teach
the API (plus a few showcase proofs), and durable `approvals/*.json` records.

Do **not** commit: regenerable dumps under `artifacts/`, font binaries built
while developing, example `out/` output beyond the showcase proofs `.gitignore`
explicitly un-ignores, or private notes. When you add an example, ignore its
`out/**` and un-ignore only the proofs worth showing in a README.

## Design rules

The hard boundaries are in
[ARCHITECTURE.md § 设计禁令与边界](docs/ARCHITECTURE.md). Two of them come up in
most reviews:

- Kernel packages (`geo` / `draw` / `system` / `project` / `plugins` / `cli`)
  stay letter-free. Letter geometry belongs to the project starter.
- When a join looks wrong, change the fragment or the element that draws it.
  Do not add a heal / blend / seal pass.

`tests/architecture/test_boundaries.py` enforces the first rule in CI.


## Human review gates

Some changes (public API surfaces, optical corrections, visual voice) are
recorded as JSON under [`approvals/`](approvals/README.md). Agents may draft
them, but only a human may set `approved: true`.
