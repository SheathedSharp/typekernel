# Starter tag noncompliance inventory

Generated against the normative grammar in `ARCHITECTURE.md` §6.3.1.
Audit surfaces the same issues as info-level `tags.grammar` findings.

**Status (live):** all three starters report **0** noncompliant tags / `tags.grammar` findings.
Inventory test: `tests/starters/test_tag_inventory.py`.

## `latin_sans` (0 noncompliant tags)

All tags now use the legal `part[.qualifier]*` forms
(`stem`/`bar`/`diag`/`hook`/`mark` plus sides, positions, faces and indices).
No illegal qualifiers remain (`tf`/`osf`/`slash`/`ray`/`arm`/`apo`/`stroke`/`j`/`m`/`h`/`v`/…).

## `latin_humanist_italic` (0 noncompliant tags)

Already clear; remeasured live — still 0.

## `latin_chancery` (0 noncompliant tags)

Already clear; remeasured live — still 0.
