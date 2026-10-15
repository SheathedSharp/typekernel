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
| 参考试作（程序） | 2026-10-15 | 库维护者 | pass | pass | pass | `design_*.py`；`voice_distance` ≈ 0.54 / 0.54 / 0.53；`tests/fixtures/tk502_reference_metrics.json` + `test_reference_metrics_match_committed_fixture` |
| 终验 | _待填_ | | | | | M5 TK-502：须独立 agent 跑 brief + **人评**（1–5） |

## 终验流程（TK-502，程序侧）

与「参考试作」不同：终验必须由**执行试验的 agent/人**从对应 brief 的 preset 出发改字，不得只跑库内 `design_*.py` 并声称完成。

**发布前程序条（库维护者，非终验本身）**：`PYTHONPATH=src python examples/run_m5_program_exit.py`（§8 + 待签 gate 的 `test_evidence`，见 `--list` / `--gate`）；或 `pytest -q tests/docs/test_development_plan_section8.py`。衬线/斜体视觉 gate 用 `examples/human_review_bundle.py` 校样后由人更新 `approvals/serif-*-voice.json`、`italic-vf-construct.json`（仍为 `approved: false` 时不得声称 M5 视觉验收完成）。

1. **固定 brief**（上表三行，文案不改）。
2. **工作目录**：`artifacts/trials/<YYYY-MM-DD>-<模型或代号>/`，内含 `brief-1/` … `brief-3/`（若 brief-2 做衬线，可另存 `brief-2-slab/` 快照，仍对照 brief-2 指标）。
3. **每个 brief**：
   - 实现 `controls()`（Regular）并记录 API（`Style` / `tuned_glyph` / `with_glyph` / `with_stem_relief`）。
   - `PYTHONPATH=src python examples/agent_trial/snapshot_design.py --brief brief-N --design <你的模块.py> --out <dir>/brief-N`
   - 审计已写 JSON：`PYTHONPATH=src python examples/agent_trial/validate_snapshot.py <dir>/brief-N/snapshot.json`
   - 检查 JSON：`program_pass_ok`（程序侧全过，含空 `cheating_flags`）、`family_gate_ok`、`metrics_ok`、`l3_voice_ok`（= `l3_voice_criteria_met`：距离 + 拓扑 + gate/lint，非纯 stem 缩放）、`topology_fraction`（≥ `L3_MIN_TOPOLOGY_FRACTION` 0.05 当 `l3_voice_ok`）、`weight_ladder_r8_failures==0`（阶梯 stem 与 TK-207 一致，含 **200**，且含试作上的改字）、`cheating_flags` 为空（纯 stem 缩放会写入 `stem_only_or_scale_voice`）。`snapshot_design.py` 在写 JSON 前跑 `validate_trial_snapshot`（拒 forged `l3_voice_ok`）；退出码 **5**=字段不一致、**6**=未达 L3、**7**=`cheating_flags` 非空。
   - 可选：`build_reference_family.py` 同 brief 产出 OTF + `proof.png`（**不得**改 `AGENT_SENTENCE`）。
4. **人评**（1–5）：可读、统一、独特、符号完整——写入本文件摘要表「终验」行；视觉接受另写 `approvals/*.json`（见 `examples/human_review_bundle.py`）。
5. **作废条件**：改过关句、改 L3/ gate 阈值、或 `cheating_flags` 非空。

库维护者回归：`test_agent_trial_reference.py`、`test_preset_brief_snapshots_pass_gate`、`tests/fixtures/tk502_reference_metrics.json`（参考试作，非终验）、`tests/docs/test_development_plan_section8.py`、`tests/qa/test_m3_exit.py`。

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

# Regular + Bold OTF + proof（三 brief 均两档字重）
PYTHONPATH=src python examples/agent_trial/build_reference_family.py \
  --brief brief-1 --out artifacts/trials/warm-humanist-family
```

设计稿：`design_warm_humanist.py`（brief-1）、`design_editorial_geometric.py`（brief-2 几何）、`design_editorial_slab.py` / `design_editorial_bracketed.py`（brief-2 衬线）、`design_coding_clear.py`（brief-3）——均达 L3 距离 + gate/R8。CI：`test_agent_trial_reference.py`；**人审**与终验摘要表仍须填写。

brief-2 衬线构建：

```bash
PYTHONPATH=src python examples/agent_trial/build_reference_family.py \
  --brief brief-2 --variant slab --out artifacts/trials/editorial-slab-family

PYTHONPATH=src python examples/agent_trial/build_reference_family.py \
  --brief brief-2 --variant bracketed --out artifacts/trials/editorial-bracket-family
```
