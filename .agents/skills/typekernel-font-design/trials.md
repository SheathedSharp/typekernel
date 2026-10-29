# Cold-start / final-acceptance checklist

For coding agents that did **not** implement typekernel. Work in an **empty
directory**. Do not open the typekernel source tree to copy answers from
`src/typekernel`.

Historical trial logs (assisted / cold-grokbot summaries) stay on the
maintainer machine in a local `docs/AGENT_TRIALS.md` (gitignored). This file is
the **tracked** checklist those agents should follow.

## Read first

1. `docs/ARCHITECTURE.md` — standard workflow and design bans
2. This skill’s `SKILL.md`, **`reference.md`** (construct + `optics.stem`),
   `recipes.md`, `anti-patterns.md`
3. This checklist

Do **not** read kernel implementation to reverse-engineer letter geometry.

## Setup

```bash
pip install -e "/path/to/typekernel[compile,specimen]"   # install only — do not edit the repo
# or: pip install "typekernel[compile,specimen]" when a tip is published
```

Ensure this skill directory is available to the agent (Cursor skill mount or copy).

## Steps

1. `tk new cold_trial --starter latin-sans` (pick any empty parent directory;
   **do not** mutate files under typekernel’s `starters/`).
2. Write `brief.md` (your own brief is fine).
3. Change only project `system.py` / `glyphs/` / `project.py` corners (record what
   you changed). Prefer `draw.construct` (`hook` / `tensioned_arc` / `spring` /
   `diagonal_band`) for hooks/arcs; use `optics.stem.measure_oriented_stem` /
   `diagonal_compensation` for diagonal optics (see `reference.md`).
4. Run and keep PNGs under the project (or a local artifacts folder):

   ```bash
   tk build .
   tk proof control .
   tk proof --text "nnonoo HHOHOO hamburgefonstiv" .
   tk proof --glyph n .
   tk audit .
   ```

5. Report: date / model, whether control glyphs look different by eye, audit
   error count, whether heal/blend/seal was used (**must be no**), whether the
   typekernel source tree was opened (**must be no**).

## Hard rules

- Letter geometry lives in the **project**; the library has no letter builders.
- Do not use heal / blend / seal.
- On failure: stop and report the command + full stderr; do not guess or patch the library.

## Pass bar

- `tk build` / `tk proof` / `tk audit` succeed (0 audit errors).
- Control string is visibly different from the stock starter for the brief you chose.
- No heal/blend/seal; no reading typekernel sources for answers.
