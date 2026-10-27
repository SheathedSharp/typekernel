---
name: typekernel-dev-norms
description: >-
  Commit-message conventions and public-OSS docs policy for typekernel. Use when
  committing, reviewing git status, writing README/VISION/API docs, deciding what
  belongs in the repo vs .gitignore, or when the user mentions conventional
  commits, ticket slang, or open-source layout.
---

# typekernel development norms

Canonical long-form: [docs/dev-standards.md](../../../docs/dev-standards.md).

## Commit messages

Use **conventional commits**. Subjects describe the human change, never internal ticket slang.

```
feat(geo): refit pathops outlines to cubics after union
fix(parts): heal self-intersections in trace_letter
docs: document OSS commit vs ignore policy
chore: ignore local ticket specimen dumps
test(geo): lock polyline-to-cubic expand path
```

Rules:

- Prefer `type(scope): summary` (`feat`, `fix`, `docs`, `test`, `chore`, `refactor`).
- **No ticket slang in the subject** — no `TK-NNN:`, no planner pack codes, no private backlog ids.
- Bodies stay short; put design rationale in docs or the PR, not in jargon.
- One logical change per commit when practical (library fix ≠ skill docs ≠ gitignore).

## What to commit (public OSS)

Track these so strangers can use and understand the library:

| Keep in git | Examples |
| --- | --- |
| Product narrative | `README.md`, `docs/VISION.md`, `docs/AGENT_GOAL.md` |
| Contributor norms | `docs/dev-standards.md`, `.agents/skills/**/SKILL.md` |
| API / recipe docs | `.agents/skills/typekernel-font-design/`, `docs/agent-recipes.md` (pointer), module docstrings, typed `__all__` |
| Examples that teach | `examples/*/build.py`, `design.py`, `README.md`, key showcase PNGs |
| Tests and fixtures | `tests/**`, small golden hashes |
| Program history (public) | `docs/DEVELOPMENT_PLAN.md`, `docs/AGENT_TRIALS.md` (summaries only) |
| Approval gate records | `approvals/*.json` (durable human decisions) |

## What must NOT be in git

| Exclude | Why / how |
| --- | --- |
| Private planner / agent scratch | `.agents/*` except tracked `skills/` and `.agents/README.md` |
| Local approval WIP / personal briefs | Keep off-tree or under ignored paths; do not invent ticket folders in-repo |
| Huge / regenerable artifacts | `artifacts/build/**`, `artifacts/specimens/**`, `artifacts/trials/**`, `artifacts/human-review/**` |
| Ticket-named specimen dumps | `artifacts/tk-*.png`, `artifacts/tk-*/` — regenerate locally |
| Font binaries from dogfood | `*.otf` / `*.ttf` / `*.woff*` (fixtures under `tests/fixtures/` may be excepted) |
| Example `out/` dumps | Ignored except a few named showcase proofs listed in `.gitignore` |
| Secrets / credentials | Never commit tokens, private keys, or session cookies |

When unsure: if a file is only useful to the author’s planner or a one-off agent trial, **do not commit it**. Summarize in `docs/AGENT_TRIALS.md` instead.

## Agent workflow checklist

1. Prefer library APIs (`typekernel.geo` / `draw` / `project` / `plugins`) over one-off hacks.
2. Before commit: `pytest -q`, `ruff check src tests`, `mypy -p typekernel` when touching typed surfaces.
3. Refresh only the showcase proofs that `.gitignore` explicitly un-ignores.
4. Write conventional subjects; refuse `TK-…` style subjects even if history has them.
5. Do not push unless the user explicitly asked to push.

## Font design process (agents)

When creating or extending faces in this repo:

1. Follow `.agents/skills/typekernel-font-design/` (ARCHITECTURE.md §4: tk new → system →
   control proofs → elements → audit → plugins → spacing → masters → build).
2. Letter geometry stays in the project starter; never resurrect `parts` / DesignContext.
3. Change fragments/elements — never heal / blend / seal.
4. Prefer examples under `examples/latin_sans_quickstart/` or `examples/zayju_letter/`.
