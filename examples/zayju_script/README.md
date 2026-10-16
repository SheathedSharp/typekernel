# ZayJu Letter Script

Florid English **letter-writing script** (花体信件书写体).

Late specimen phrase (after the charset is designed under gates):

> zayju Discover everywhere

## Designer order (required)

This example is **not** phrase-first. Agents must not define `BRIEF_SENTENCE` and
then `build_charset()` as the design method (that helper is **deprecated** and warns).

1. **Control glyphs** — `a` (entry/exit rails + bowl), then `o` (bowl).
2. **One letter at a time** along `DESIGN_ORDER` in `design.py`.
3. After each letter, unlock via library `DesignSequence.try_add` (style-check vs control + previous).
4. Only when the sequence unlocks the full charset compose spacing/kern and the
   brief PNG specimen.

Shared constants (`NIB_*`, `ENTRY_Y` / `EXIT_Y`) are necessary but **not
sufficient** — adjacent style checks catch drift the constants miss.

## Honest topology

This is **not** a slanted humanist/sans with `lean` / `oblique_font` / tracking.
Each glyph is a calligraphy **skeleton** expanded with a contrast nib via
`trace_letter` (library heal / strip / cubic refit). Writing slant is baked into
centerline coordinates. Shared entry/exit rails aim at semi-connected writing.

Charset: letters in `DESIGN_ORDER` plus space. Semi-connected flourishes — not a
full connected copperplate family.

## Build

```bash
pip install -e ".[compile,specimen,boolean]"
PYTHONPATH=src python examples/zayju_script/build.py
```

`build.py` exits non-zero if the sequential style gate fails.

Outputs under `out/`:

| File | Role |
| --- | --- |
| `ZayJuLetterScript-Regular.otf` / `.ttf` | Installable Regular |
| `sentence_brief.png` | Late specimen phrase (filled composition) |
| `sentence_brief_display.png` | Late specimen (display size) |
| `grid.png` | Used-letter inventory |
| `glyph_*.png` | Per-glyph checks |


## Style gate budgets

`script_sequence_tolerances()` keeps rails/slant/stem near body defaults.
Contrast allows multi-vertical pen stress (`u`/`h`). Role skips omit metrics
that topology makes meaningless (closed bowls, ascenders, descender loops,
dotted `i`/`j`). Glyphs that failed those budgets were redesigned one letter at
a time — not unlocked by widening the gate.

## Gates

- **Required:** `build_charset_sequential` → library `typekernel.qa.DesignSequence` (style
  consistency vs control + previous).
- Controls `check_sentence_gate` does **not** apply — this face is not derived
  from `Controls.build_all`.

## Files

- `design.py` — metrics, `DESIGN_ORDER`, per-glyph skeletons, sequential builder
- `build.py` — style gate, space, phrase kern, compile, proofs
