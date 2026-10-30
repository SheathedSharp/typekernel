# Cold-start / final-acceptance protocol 

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

## Fixed briefs (run all four)

| ID | Brief | Masters |
| --- | --- | --- |
| B1 | Warm humanist UI sans (readable UI copy) | Regular + Bold |
| B2 | Editorial slab serif | Regular + Bold |
| B3 | Programming monospace with full ASCII punct | Regular (+ Bold optional) |
| B4 | Flowing letter-hand / connected script (cold: `zayju forever young`) | Regular |

Each brief is a fresh `tk new` project under the empty parent. Do not mutate
files under typekernel’s `starters/`.

**B4 notes:** prefer starter `script-roundhand` (or `latin-chancery`) so
entry/exit joins and `Metrics.join` are in play. Sample proof/critique text
is exactly `zayju forever young`. Do **not** invent human SCORE numbers —
leave readable / unified / distinctive / complete blank for a human.

## Required actions (per brief)

1. `tk new <name> --starter latin-sans` (or another public starter if the brief
   needs it; record which).
2. Write `brief.md` matching the fixed brief above.
3. **Draw ≥5 new glyphs** (new `@glyph` sources — not only `System` token tweaks).
4. **Switch style once** (corners / ends / a style plugin, or swap a construct
   family) and record the switch.
5. Author **two masters** (Light↔Bold or Regular↔Bold designed deltas).
6. Add **≥10 composites** (accents / digraphs via project compose / charset).
7. Prefer `draw.construct` (`hook` / `tensioned_arc` / `spring` / `diagonal_band`)
   and `optics.stem` helpers (see `reference.md`).

## Commands to keep

```bash
tk build .
tk proof control .
tk proof --text "nnonoo HHOHOO hamburgefonstiv 0123456789.,;:!?()[]" .
tk proof --glyph n .
tk audit .
tk read --text "zayju forever young" .
tk critique --text "zayju forever young" .
```

For **B4**, also keep:

```bash
tk proof --text "zayju forever young" .
tk audit --text "zayju forever young" .
tk critique --text "zayju forever young" .    # objective self-score table
```

Keep PNGs / audit JSON under the project (or a local artifacts folder).

## Record (per brief)

| Field | Content |
| --- | --- |
| date / model | |
| rounds | how many edit→build→audit loops |
| audit errors | count + top codes |
| expect.py edits | what changed and **why** |
| review notes | short observations |
| human scores 1–5 | readable / unified / distinctive / complete |

## Hard rules

- Letter geometry lives in the **project**; the library has no letter builders.
- Do not use heal / blend / seal.
- On failure: stop and report the command + full stderr; do not guess or patch the library.
- Do not open typekernel sources for glyph answers.

## Pass bar

Program-side (agents must meet these; cite `tk critique` in ACCEPTANCE):

1. **Readable**: `tk critique --text "…"` `read.identity` level `ok` (0 hard warns) on the brief sample string.
2. **Joined** (B4 / script): critique `join.dy` ok (max Δy &lt; 20) and `join.rhythm_cv` ok on that string.
3. **Clean contours**: critique `contour.quality` not `fail`; no flood of contour warns on the sample glyphs.
4. `tk build` / `tk proof` / `tk audit` succeed (**0 audit errors**). Audit-green alone is **not** enough.
5. Every `expect.py` change has `--expect-change` / `expect_changes` rationale.
6. B4: critique for `zayju forever young` is cited; **human SCORE columns stay blank**.
7. No heal/blend/seal; do not open typekernel sources for glyph answers.
8. Control string visibly different from the stock starter for that brief.

Human-side (not claimed by agents):

- After human scoring: **readable** and **complete** averages ≥ 3.5 and above the recorded baseline.
- Vision approve remains human-only.

## Related

- baseline / final runs: same checklist; store scores with the trial log.
- LihuiT dogfood: see `dogfood/lihuit/README.md` (separate transplant workspace).

## B4 SCORE_TABLE (program + human)

Cold prompt: flowing letter-hand; sample string `zayju forever young`.
Program columns come from `tk critique` (cite in ACCEPTANCE self-critique).
Human columns stay blank until a person scores.

| Field | Value |
| --- | --- |
| date / model | |
| starter | script-roundhand (or note swap) |
| rounds | |
| audit errors / warns | |
| critique read.identity | |
| critique join.* / gap_dist | |
| critique contour.quality | |
| expect.py edits + why | |
| human SCORE readable (1–5) | |
| human SCORE unified (1–5) | |
| human SCORE distinctive (1–5) | |
| human SCORE complete (1–5) | |
| vision approve | |

## status (maintainer)

Protocol above is tracked. Program-side cold runs may drop SCORE_TABLE/RECORD under `transplants/trials/<date>-*/` (those summaries are tracked; PNGs stay gitignored). **Human 1–5 scores** and vision approve remain required for the P6-2 pass bar — agents leave those cells blank. See `transplants/trials/README.md`.

### Honesty (2026-10-29 / updated)

- **B4 program archival (tracked):** `docs/trials/2026-10-29-b4-cold-zayju/` — ACCEPTANCE excerpt, PROGRAM_METRICS, SCORE_TABLE with human cells blank.
- That is **not** VISION approve and **not** a filled human SCORE table.
- Agents must still leave human SCORE blank and must not write `approved: true`.
