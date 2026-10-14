# Agent 试验记录

固定协议见 [`DEVELOPMENT_PLAN.md`](DEVELOPMENT_PLAN.md) 第 6 节。brief 文案**不得**因试验结果改写。

## 三个 brief

| ID | 标题 | 起始 preset |
| --- | --- | --- |
| `brief-1` | 温暖的人文主义 UI 无衬线（Regular + Bold） | `humanist_sans` |
| `brief-2` | 编辑排版几何无衬线（单层 a/g；衬线待 TK-306） | `geometric_sans` |
| `brief-3` | 编程/UI 清晰体 + 全 ASCII 标点 | `code_clear` |

## 每次试验必须记录

- 使用的 API：`tuned_glyph` / `with_glyph` / `with_stem_relief` / `Style`（后两者待落地）
- 轮次、lint/identity 错误数、`voice_distance`、字重阶梯 R8 失败数
- 是否换过关句或改阈值（**有则试验作废**）
- 人对 contact sheet 评分（1–5）：可读、统一、独特、符号完整

程序快照：`typekernel.qa.trial_protocol.snapshot_trial` → JSON。

## 基线 / 终验目录

大文件与校样图：`artifacts/trials/<日期>-<模型>/`（已 gitignore）。本文件只保留**摘要表**。

| 阶段 | 日期 | 模型 | brief-1 gate | brief-2 gate | brief-3 gate | 备注 |
| --- | --- | --- | --- | --- | --- | --- |
| 基线 | _待填_ | _待填_ | | | | M1 后首次跑 |
| 终验 | _待填_ | | | | | M5 TK-502 |

## 跑预设基线快照（库维护者）

```bash
python examples/agent_trial/snapshot_presets.py --out artifacts/trials/preset-baseline
```

输出每个 preset 的 `snapshot.json`（未改动的 `Controls.from_context`），用于对比 agent 试验是否真有 voice 距离。
