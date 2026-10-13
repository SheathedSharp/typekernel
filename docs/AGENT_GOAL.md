# typekernel — Coding Agent 产品目标

## 定位（一句话）

**typekernel 的定位应该是让 coding agent 通过使用这个基础库，像人类字体设计时一样去创建一种字体「包括各个字重，符号等等」。**

## 这意味着什么

| 人类字体设计师 | Agent 通过 typekernel 应对齐的行为 |
| --- | --- |
| 先定 brief / 比例 / 字族性格 | 选或调 `DesignContext`（preset + 有记录的 override），写清 family 用途 |
| 画 control 字（n/o、H/O）再扩族 | `Controls.from_context` → 验证 control → `build_all()`，不是逐字随机堆轮廓 |
| 每个字重是 **重画母版**，不是描粗 | 每个 `wght` 独立 `Controls`（stem + `with_stem_relief()` 等 **designed delta**） |
| 斜体是 **另一套母版** | `italic_controls()` + `Master({"ital":1})`；机械 oblique 仅作 `slnt`，不得冒充 italic 名 |
| 符号、数字、变音属于同一族 | 标点 / figures / extended Latin / 特性 glyph 与 `features.fea` **同时存在** |
| 侧距与字偶是设计的一部分 | `space_font` → class kern；VF 各母版 **同一 kern groups** |
| 用句子 proof 验收 | 编译 OTF/TTF 后 `qa.proof`；`qa.sentence_gate.check_sentence_gate(controls)` 在 CI 回归 |
| 特性与 glyph 一致 | 优先 `compose_font_from_controls` + `FamilyBuildOptions`，避免幽灵 `.tf`/`.case` |
| 单字 master | `Controls.with_glyph(ch, builder)` 替换派生，而非只拧 context |

## 不是什么

- 不是「调几个 float 就得到任意书法 / 花体」——**品类**（sans / serif / script）由 **拓扑与 glyph 集** 决定，缺拓扑要扩 `parts` 或 import UFO，而不是 shear。
- 不是 fontmake 替代品：OpenType 表与二进制编译 **依赖 fontTools / ufo2ft**。
- 不是可跳过 proof 的导出脚本：能安装 ≠ 设计完成。

## 成功标准（Agent 交付前自检）

1. **字族完整**：Regular + 至少 Light/Bold 或 VF 轴覆盖；italic 若承诺则 designed masters。
2. **字符集声明与实现一致**：`build_all` 子集、`features`、UFO 里 glyph 名一致（无 `.tf` / `.case` 幽灵引用）。
3. **可读 proof**：用户给定或 brief 中的 **整句** 在正文字号（约 24–36 px）下无明显断笔、撞字、字偶洞。
4. **可复现**：`examples/<name>/build_*.py` 或等价脚本一键 build；依赖 `[compile,specimen]` 写进 README 片段。

## 维护

- Agent 工作流说明书： [`.agents/skills/typekernel-font-design/SKILL.md`](../.agents/skills/typekernel-font-design/SKILL.md)
- 改 `parts` / `compile` / 推荐管线时，**同步更新** 该 skill 与本文（若目标变化）。
