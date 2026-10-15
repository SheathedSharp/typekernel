# Agent 试验记录

固定协议见 [`DEVELOPMENT_PLAN.md`](DEVELOPMENT_PLAN.md) 第 6 节。brief 文案**不得**因试验结果改写。

## 三个 brief

| ID | 标题 | 起始 preset |
| --- | --- | --- |
| `brief-1` | 温暖的人文主义 UI 无衬线（Regular + Bold） | `humanist_sans` |
| `brief-2` | 编辑排版几何无衬线（单层 a/g）；衬线 voice 用 `slab_serif()` / `bracketed_serif()` | `geometric_sans` |
| `brief-3` | 编程/UI 清晰体 + 全 ASCII 标点 | `code_clear` |

## 每次试验必须记录

- 使用的 API：`tuned_glyph` / `with_glyph` / `with_stem_relief` / `Style`（`parts.style.Style`）
- 轮次、lint/identity 错误数、`voice_distance`、字重阶梯 R8 失败数
- 是否换过关句或改阈值（**有则试验作废**）
- 人对 contact sheet 评分（1–5）：可读、统一、独特、符号完整

程序快照：`typekernel.qa.trial_protocol.snapshot_trial` → JSON。

## 基线 / 终验目录

大文件与校样图：`artifacts/trials/<日期>-<模型>/`（已 gitignore）。本文件只保留**摘要表**。

| 阶段 | 日期 | 模型 | brief-1 gate | brief-2 gate | brief-3 gate | 备注 |
| --- | --- | --- | --- | --- | --- | --- |
| 基线（M1） | 2026-10-14 | 库维护者 | fail | fail | fail | `artifacts/trials/preset-baseline-2026-10-14/`（R1/引号等问题，已过时） |
| 基线（M2） | 2026-10-14 | 库维护者 | pass | pass | pass | `artifacts/trials/preset-baseline-2026-10-14-gate-clear/`；CI：`test_preset_brief_snapshots_pass_gate` |
| 终验 | _待填_ | | | | | M5 TK-502 |

## 跑预设基线快照（库维护者）

```bash
python examples/agent_trial/snapshot_presets.py --out artifacts/trials/preset-baseline
```

输出每个 preset 的 `snapshot.json`（未改动的 `Controls.from_context`），用于对比 agent 试验是否真有 voice 距离。

衬线 L3 voice 基线（`slab_serif` / `bracketed_serif`，brief-2 上下文）：

```bash
PYTHONPATH=src python examples/agent_trial/snapshot_serif_voices.py --out artifacts/trials/serif-voices
```

CI 覆盖：`test_serif_voice_trial_snapshots_meet_l3`（`tests/qa/test_trial_protocol.py`）。

brief-1 **改字**参考（`Style` + `tuned_glyph`，非 preset 快照）：

```bash
PYTHONPATH=src python examples/agent_trial/snapshot_design.py \
  --brief brief-1 --out artifacts/trials/warm-humanist-ref
```

设计稿：`examples/agent_trial/design_warm_humanist.py`（brief-1 参考已达 L3 距离 + gate/R8）。CI：`test_agent_trial_reference.py`；**人审**与终验摘要表仍须填写。
