# Legacy examples (quarantined)

These directories taught **Usage B**: `Controls` + `DesignSequence` / `unlock_*` /
`build_all` as the only legal design path.

**Product rule now:** typekernel is a **composable parts toolbox**. Agents write
Python that composes parts → `Font` → agent-chosen spacing → compile → proof
(**Usage A** only). Aggregate family factories are not the happy path.

| Path | Former role | Fate |
| --- | --- | --- |
| `agent_studio/` | L0 trial forcing DesignSequence | quarantine → delete |
| `agent_family/` | L2 family via Controls factory | quarantine → delete |
| `agent_catalog/` | Controls-first API index | quarantine → delete |
| `agent_trial/` | trial protocol / snapshots | quarantine → delete |
| `agent_glyph_preview/` | Controls preview helper | quarantine → delete |

Do **not** copy these as templates for new faces. See
`.agents/skills/typekernel-font-design/` and `examples/first_font/` (compose /
proof demos; prefer parts composition over `Controls.build_all` for new work).

Tests may still import these paths until they are deleted.
