# Removed: correspondence anti-pattern

This folder previously tried to fake “letter script” by tuning humanist sans
parameters. That mis-set agent expectations.

**Do instead**: follow
[`.agents/skills/typekernel-font-design/SKILL.md`](../../.agents/skills/typekernel-font-design/SKILL.md)
and [`docs/AGENT_GOAL.md`](../../docs/AGENT_GOAL.md). Use `Controls` +
`compose_font_from_controls`; for a new voice, add glyph topology or import UFO.

Local `out/` artifacts are ignored by git.
