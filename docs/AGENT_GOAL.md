# typekernel — Coding Agent 产品目标

## 定位（一句话）

**typekernel 是给 coding agent 用的可组合零件工具箱**：用 Python 拼零件 → 成字 → 自选间距 → 编译 → 校样，从而像人类字体设计一样做出字族（多字重、符号、斜体等）。

## 唯一合法用法（Usage A）

```
parts / letter builders → Font → space（agent 自选）→ build_font → proof
```

Agent **必须**用代码表达 brief、比例与字形决策（`DesignContext`、零件、`GlyphAssembler` / letter builders、`with` 手改轮廓等），再编译与 proof。

| 人类字体设计师 | Agent 应对齐的行为 |
| --- | --- |
| 先定 brief / 比例 / 性格 | 选或调 `DesignContext`（preset + 有记录的 override） |
| 画字母、改结构 | 用 `typekernel.parts` 零件与 letter builders **自己拼** |
| 每个字重是重画母版 | 每档独立 context + 重拼字形（不是描粗） |
| 斜体是另一套母版 | `italic_design` / 自建斜体拓扑；不要用机械 shear 冒充 Italic |
| 侧距与字偶是设计的一部分 | `space_font` 或手写 advance / kern（**agent 自选**） |
| 用句子 proof | `qa.proof` / waterfall；人审 JSON 由人签 |

## 杀掉的用法（Usage B）

以下 **不是** 产品快乐路径，文档与 skill 不再教它们当设计方法：

- `FormSources.build_all` / 整句 charset 批量当设计
- `DesignSequence` / `unlock_*` 当作「唯一合法设计」
- `examples/_legacy/agent_studio|agent_family|…` 当模板
- 把 aggregate family factory 当「快捷糖」保留双轨教学

`FormSources` 等模块可暂时留在库里供旧测试；计划隔离删除。新面子请走 Usage A。

## 完成分级

| 级别 | 完成条件 |
| --- | --- |
| **试字** | 有 brief；至少用 **两种** 不同拼法想过同一 brief（见 skill）；关心的字在代码里拼出；有 proof |
| **单 style 可读** | 声明字符集拼齐；间距自选；`build_font` 成功；瀑布/pair 可读 |
| **字族** | 每字重（及承诺的斜体）独立母版；VF 时共用 kern groups；每母版有校样 |

人审 `approvals/*.json` 仍须人签；**不要**擅自把 `approved` 改成 true。

### 反模式

见 [`.agents/skills/typekernel-font-design/anti-patterns.md`](../.agents/skills/typekernel-font-design/anti-patterns.md)：描粗当字重、shear 当斜体、死旋钮、aggregate 当设计、无字形的特性。

## 从哪开始

```bash
pip install -e ".[compile,specimen,boolean]"
```

- Skill：[`.agents/skills/typekernel-font-design/SKILL.md`](../.agents/skills/typekernel-font-design/SKILL.md)（含同一 brief 的 ≥2 种配方）
- 零件表：`parts-catalog.md`；配方：`recipes.md`
- 示例方向：`examples/first_font/`、`examples/zayju_letter/`（优先学零件拼装，而不是 FormSources 工厂）

## 工程债 / 程序验收（维护者）

脚手架与部分默认构造仍在库内；视觉终验仍靠人。程序入口：

- `PYTHONPATH=src python examples/run_program_exit.py`
- `examples/human_review_bundle.py`（`--only appendix-b` 或 `--only serif|italic` → 含 `appendix_b_three_g_humanist.png`）
- `examples/contact_sheet.py`、`examples/regenerate_outline_hashes.py`、`examples/diff_overlay.py`
- 试验快照：`examples/_legacy/agent_trial/validate_snapshot.py`（legacy）
- 烟测指针：`test_knob_coverage`、`test_extended_latin_policy`、`test_multi_voice_exit`、`test_style_consistency`、`test_originality`、`test_stress`、`test_glyph_specs`、`test_stroke_program_acceptance`、`test_zayju_script`、`test_serif_voice_meets_program_acceptance`

配方指针与维护 CLI：[agent-recipes.md](agent-recipes.md)。旧 FormSources 菜谱：[docs/_legacy/agent-recipes.md](_legacy/agent-recipes.md)。

## 维护

改 `parts` / `compile` / 推荐管线时，**同步更新** skill 与本文。
