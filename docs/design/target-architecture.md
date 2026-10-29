# typekernel 目标架构（v1 草案）

> **状态**：设计草案，尚未实现。现行契约仍以 [`ARCHITECTURE.md`](../ARCHITECTURE.md) 为准；
> 本文某一节落地后，把该节并入 `ARCHITECTURE.md` 并从本文删除，避免两份真相。
> **执行计划**：维护者本地的 `docs/design/roadmap.md`（不随仓库分发）；阶段与验收以那份为准。
> **依据**：2026-10-29 审查——实测三个 starter 的样张、`font.py` 切 slab、通读内核代码。
> **不变的前提**：第一性原理仍是「人类字体设计师怎么做，agent 就怎么做」；内核不出现字母名；
> 不事后修缝；编译全部复用 fontTools；Oblique ≠ Italic；字重是 designed deltas。

---

## 0. 为什么要改

| 审查现象 | 根因 | 本文对应 |
| --- | --- | --- |
| `e` 像 θ、`3` 像 8、`(` 是墨块，`tk audit` 仍报 0/0 | 审计只量 stem / zone / 方向 / 兼容，不懂字腔拓扑；starter 用「圆环 + 矩形」拼字 | §4 解剖构件、§7 诊断 |
| `n` 平顶像 п | 肩从 x 高处以水平切线离干，缺少设计师的「接干深度」与削薄 | §4.3 `arch` 契约 |
| 按文档切 `slab` 只得到斜向小凸块；给 `*.top.*` 再挂 slab 时 build 直接报错 | 86 个字形文件里只有 9 个声明角点槽；填充器假设两侧是直线边；插件契约只测拓扑不测语义 | §9 槽位与插件 v2 |
| 做不了重音字母、特性、静态实例 | `@glyph` 只能返回 `Drawing`；`Project` 没有组件、锚点、特性、轴、实例模型 | §3、§10、§11 |
| 内核里有 `"v","w",…,"zero","seven"` 和 `{"o","O","c","e"}` | 检查按字母名分支；守卫只扫函数名 | §5.4 traits、§14 守卫 |
| 多个项目在同一进程里串扰；配置散落在 `system.py` 的模块级变量中 | 用裸模块名 `system` / `elements` 导入；约定是隐式魔法名 | §3.5 `ProjectSession`、§3.2 清单 |
| `System.tokens` 里有约 140 个逐字宽度 / 步进值，同时存在两套 advance 来源 | `System` 兼任逐字数据表 | §5 数值表与度量 |
| agent 只能看编译后的文本渲染 PNG | 没有编辑视图、没有结构化测量输出，必须先编译 | §6 感知 |
| 「视觉门」实际退化成「附了图就算过」 | 评审没有记录、没有时效、和轮廓哈希无关 | §8 评审 |

---

## 1. 目标能力（每条都可测）

| 编号 | 能力 | 可测标准 |
| --- | --- | --- |
| **C1 看得见** | agent 能看到设计师在编辑视图和样张里看到的一切，不必先编译 | `tk see` 单字 < 1 s；输出 PNG + 同名 JSON（节点、标签、度量、测量值） |
| **C2 画得对** | 字形代码表达结构；解剖构件把手艺编码进去；拓扑错误在书写或诊断阶段暴露 | 每个解剖构件有几何语义契约测试；starter 全字符集满足期望表 |
| **C3 判得准** | 诊断覆盖结构、拓扑、垂直度量、笔画、间距、灰度、插值、发布；美学交给评审并留记录 | 2026-10-29 审查登记的缺陷中，可客观检测的全部被报出 |
| **C4 出得全** | 字符集、组合字、特性、轴 / 实例、斜体家族链接、垂直度量、发布检查 | latin-sans 覆盖 Latin-1 + Ext-A，wght 100–900 VF + 9 个静态实例，FontBakery opentype profile 0 FAIL |
| **C5 改得动** | 局部改动、按母版覆盖、显式微调、前后对比、评审过期提示 | 改一个字形只让该字形（和依赖它的组合字）的评审变成 stale |
| **C6 守得住** | 内核与文字系统无关、没有字母名；文档如实；验收靠真实 agent 试验 | 守卫覆盖字符串字面量；文档链接与符号可解析；零上下文试验记录 |

---

## 2. 分层与依赖

```
┌──────────────────────────────────────────────────────────────────────┐
│ 项目（agent / 用户拥有）                                               │
│ brief.md project.py system.py elements.py glyphs/ marks/ composites.py │
│ spacing.py expect.py features/ proofs.py reviews/ approvals/           │
└───────────────────────────────▲──────────────────────────────────────┘
                                │ 只用公开 API
┌───────────────────────────────┴──────────────────────────────────────┐
│ 插件：corners / ends / passes / construct / checks / spacing           │
└───────────────────────────────▲──────────────────────────────────────┘
┌───────────────────────────────┴──────────────────────────────────────┐
│ 内核                                                                   │
│ L0 geo        曲线、轮廓、布尔、测量（现有）                            │
│ L1 draw       Fragment / Writer / Drawing / slots / construct / Measure │
│ L1.5 anatomy  新：字母无关的解剖构件（轮廓构件 + 笔构件）               │
│ L2 system     System / Zones / Intent（瘦身）                           │
│ L3 project    Project 清单、GlyphSpec v2、GlyphDraft、compose、Session  │
│ L3 metrics    新：metrics keys 引擎、kerning 模型、装箱策略             │
│ L3 axes       轴、母版、实例、家族（扩展现有）                          │
│ L3 features   新：命名后缀语法 → GSUB；fea 汇编                         │
│ L3 font       字体模型（现有）                                          │
│ L4 perceive   新：从 Drawing 直接渲染、编辑视图、样张、测量（吸收 qa.proof）│
│ L4 diagnose   新：检查引擎、Finding v2、基线（吸收 cli/audit 逻辑）     │
│ L4 review     新：评审记录、过期判定、人工批准（吸收 qa.gates）         │
│ L5 compile    UFO / designspace / fontTools + 实例 / STAT / 垂直度量    │
│ 壳 cli        只做参数解析和调用，不放逻辑                              │
└──────────────────────────────────────────────────────────────────────┘
```

依赖规则（守卫强制，见 §14）：

1. 低层不 import 高层；`cli` 可以 import 一切，但任何模块都不能 import `cli`。
2. `anatomy` 只依赖 `geo` / `draw` / `system` / `optics`。
3. `perceive` / `diagnose` / `review` 不 import `compile`（读二进制字体时用 fontTools 只读）。
4. 插件只依赖内核，插件之间互不 import（沿用）。
5. `starters/` 是模板数据，任何内核模块都不 import（沿用）。

---

## 3. 项目模型

### 3.1 目录

```
myfont/
  brief.md          # 散文 brief
  project.py        # 唯一入口：PROJECT = Project(...)
  system.py         # System 与母版数值（只是数据）
  elements.py       # 项目自己的构件组合（调用 anatomy / construct）
  glyphs/**.py      # @glyph
  marks/**.py       # @glyph(..., traits={"mark"})
  composites.py     # 组合字声明（数据）
  spacing.py        # METRICS / KERNING（数据，不再含引擎代码）
  expect.py         # 期望表：每个字形的拓扑与触区期望（数据）
  features/*.fea    # 手写特性片段（可选）
  proofs.py         # 项目自定义样张串（可选）
  reviews/          # 评审记录（agent 或人）
  approvals/        # 人工批准（发布门）
  build/ proofs/    # 生成物，gitignore
```

### 3.2 `Project` 清单（规范性签名）

`project.py` 必须导出 `PROJECT`。旧的模块级约定（`FAMILY_NAME`、`STYLE_NAME`、`MASTER_LOCATIONS`、
`AUDIT_STEMS`、`EXTRA_CHECKS`、`BRIEF`、`spacing.apply_spacing`、`font.get_project`）全部删除，
加载器遇到时报迁移错误，不做兼容双轨。

```python
@dataclass(frozen=True, slots=True)
class FamilyInfo:
    family: str
    designer: str = ""
    version: str = "0.001"
    vendor: str = ""            # OS/2 achVendID
    license: str = ""
    license_url: str = ""
    copyright: str = ""

@dataclass(frozen=True, slots=True)
class Project:
    info: FamilyInfo
    system: System                                  # 默认母版的 System
    glyphs: str | Path = "glyphs"
    marks: str | Path | None = "marks"
    axes: Sequence[Axis] = ()                       # §10
    masters: Sequence[MasterSpec] = ()              # §10；空 = 单母版
    instances: Sequence[Instance] = ()              # §10；空 = 由轴自动生成命名实例
    charset: Charset | None = None                  # 声明要交付的字符；诊断按它算覆盖率
    composites: Mapping[str, Composite] = {}        # §3.4
    corners: Mapping[str, CornerFiller] | None = None
    ends: Mapping[str, EndFiller] | None = None
    metrics: Metrics | None = None                  # §5.3
    kerning: Kerning | None = None                  # §5.3
    features: Features = Features()                 # §11
    expect: Mapping[str, Expect] = {}               # §7.3；项目期望表
    audit: AuditConfig = AuditConfig()              # §7
    proofs: ProofConfig = ProofConfig()             # §6
    review: ReviewPolicy = ReviewPolicy()           # §8
    brief: Brief | None = None                      # typed intent（现有）
```

`Project` 只是声明。求值、构建、诊断由 `ProjectSession`（§3.5）完成，`Project` 本身不再有
`discover()` / `evaluate()` 之类的可变状态。

### 3.3 `GlyphSpec` v2 与 `GlyphDraft`

```python
def glyph(
    name: str,
    *,
    unicodes: Sequence[int] | None = None,   # None = 按 AGL / 单字符推导；() = 不编码
    group: str = "",
    traits: Iterable[str] = (),              # 字母无关的形态标记，§5.4
    expect: Expect | None = None,            # 覆盖项目期望表中同名条目
) -> Callable[[GlyphFn], GlyphFn]: ...

GlyphFn = Callable[[System], "Drawing | GlyphDraft"]

@dataclass(frozen=True, slots=True)
class GlyphDraft:
    drawing: Drawing
    anchors: Mapping[str, PointLike] = {}    # "top" / "_top" / "bottom" / "ogonek" …
    components: Sequence[ComponentRef] = ()  # 手工组件（一般用 composites.py）
    note: str = ""                           # 设计意图一句话；进 tk explain
```

规则：

- 返回 `Drawing` 等价于 `GlyphDraft(drawing)`。
- 锚点名不做语义校验；组合字引用了不存在的锚点时，诊断报 error。
- `traits` 和 `expect` 是诊断的输入，不影响几何。
- `@fn.master(name)` 沿用；覆盖函数返回值类型同上。

### 3.4 组合字 `compose`

```python
@dataclass(frozen=True, slots=True)
class Composite:
    base: str                                # 基字形名
    marks: Sequence[str]                     # "acutecomb@top"：mark 名 @ 基字形锚点名
    unicodes: Sequence[int] | None = None    # None = 按名字推导

def compose(spec: Composite, glyphs: Mapping[str, Glyph]) -> Glyph
```

- 对齐规则：mark 的 `_<anchor>` 对到 base 的 `<anchor>`；mark 叠 mark 时用上一个 mark 的同名锚点（mkmk 语义）。
- advance 取基字形的值；组合字自身的锚点由基字形继承，再加上 mark 的非下划线锚点（可继续叠加）。
- 大写用 `.case` 变体的规则写在 starter 的 `composites.py` 里（数据），内核不知道「大写」。
- Latin-1 / Ext-A 的组合表属于字母数据，放在 starter，拷进项目后归项目所有。

### 3.5 `ProjectSession`（加载语义）

```python
@contextmanager
def open_project(root: str | Path) -> Iterator[ProjectSession]: ...

class ProjectSession:
    project: Project
    def specs(self) -> Mapping[str, GlyphSpec]
    def evaluate(self, name: str, *, master: str | None = None, slots: bool = True) -> GlyphDraft
    def glyph(self, name: str, *, master: str | None = None) -> Glyph      # 含度量装箱
    def font(self, *, master: str | None = None) -> Font                  # 含组合字、kerning、features
    def reload(self) -> set[str]                                          # 返回失效的字形名
```

语义：

1. **隔离导入**：进入 session 时，在 `sys.meta_path` 最前面插入一个只认本项目根目录的 finder，
   把项目内的顶层模块（`system`、`elements`、`spacing` …）映射成 `_tkproj_<hash>.<name>`；
   字形文件里写的 `from elements import arch` 不用改。退出 session 时移除 finder 和这些模块。
   同一进程里交替打开两个项目，互不影响。
2. **失效**：按 `(mtime_ns, size, sha1)` 判断文件变化，不再删 `__pycache__`。`reload()` 只重新导入
   变化的模块以及 import 了它们的模块，并返回受影响的字形集合（给 `tk see --watch` 和评审过期判定用）。
3. **求值缓存**：以 `(glyph, master, 依赖模块指纹)` 为键缓存 `GlyphDraft`。
4. **错误定位**：字形函数或槽位填充抛出的异常统一包装成 `GlyphBuildError(glyph, master, tag?, cause)`。

### 3.6 `Charset`

```python
@dataclass(frozen=True, slots=True)
class Charset:
    codepoints: frozenset[int]
    extra_names: frozenset[str] = frozenset()   # 未编码字形：.case、.ss01、f_i …
    @classmethod
    def from_text(cls, path: str | Path) -> Charset   # 每行一个字符、U+XXXX 或字形名
    def __or__(self, other: Charset) -> Charset
```

starter 自带 `charset/latin-core.txt`、`latin-1.txt`、`latin-ext-a.txt`（数据）。诊断按 `charset`
报缺失和多余；`tk status` 按 Unicode 区块显示覆盖率。

---

## 4. 解剖构件 `typekernel.anatomy`（新）

### 4.1 定位

`draw.construct` 是几何原语（弧、超椭圆象限、钩），太底层，每个 starter 都在重新发明肩和碗，
结果质量不及格。`anatomy` 提供**设计师语义的结构件**：肩、碗、接干、开口碗、横杠、斜笔对顶点、
脊、钩尾、点、泪滴。它们仍然字母无关——「肩」不是字母，`n` / `h` / `m` / `r` 都用它。

边界（守卫和评审都要查）：

- 构件返回**一个结构件**的 `Drawing`，不返回整字，也不提供「组装一个字」的函数。
- 参数是几何量或设计量（厚度、接干深度、应力角、张力、开口角），不接收字形名。
- 构件自动带上标准标签（§4.2）、槽位（脚 / 顶 / 端点）和可测量声明（`Measure`，§4.4），
  因此风格插件和诊断能覆盖每一个用构件画出来的字。
- 构件不读 `System`；由项目的 `elements.py` 把 `System` 数值传进来。这样构件的契约测试不依赖任何字体。

### 4.2 标签语法（规范性）

> **已落地** → [`docs/ARCHITECTURE.md`](../ARCHITECTURE.md) §6.3.1；解析器 `typekernel.anatomy.tags`；诊断 `tags.grammar`。

### 4.3 构件清单与几何语义契约

所有构件都满足：轮廓闭合、方向正确、曲线接合 G1（声明的角点除外）、同一组参数在合法范围内
变化时 `signature()` 稳定（可插值）。下面只列各自额外的语义契约。

| 构件 | 签名要点 | 语义契约（合成形状测试） |
| --- | --- | --- |
| `stem` | `stem(x0, x1, y0, y1, *, name, foot="slot", top="slot")` | 宽度 = `x1-x0`；`foot` / `top` 两端各产生一对角点槽（`.o` / `.i`）；`Measure("stem", …)` 自动声明 |
| `arch` | `arch(stem_face_x, right_outer_x, *, height, thick, thin, join_depth, tension, crown_shift=0.0, overshoot=0.0)` | 外沿在 `y = height - join_depth` 处以竖直切线离开干面；冠点 y ∈ `[height, height+overshoot]`；接干处最薄厚度 = `thin ± 1`；右侧落到右干时竖直切线；`crown_shift` 让冠点偏右（大多数无衬线如此） |
| `bowl` | `bowl(center, rx, ry, *, thick, thin, stress_deg=0.0, exponent=2.0, overshoot=0.0)` | 水平方向（左右）实测厚度 = `thick`，垂直方向（上下）= `thin`；应力轴相对竖直旋转 `stress_deg`；外轮廓 y 极值越过区线 `overshoot` |
| `bowl_join` | `bowl_join(stem_face_x, center, rx, ry, *, side, thick, thin, crotch, …)` | 碗从干面出发（b d p q 一类），接干处削薄到 `crotch`；不产生字腔里的细缝 |
| `open_bowl` | `open_bowl(center, rx, ry, *, thick, thin, aperture: tuple[float, float], terminal_angle, bar: BarSpec \| None = None, …)` | 开口按角度区间去掉；两端是**端点槽**（交给 ends 插件）；产生 `aperture.0.a/b` 标签；`bar` 不为空时横杠只连接碗的左内壁到开口下沿，结果是 **1 个闭合字腔 + 1 个开口**（`e` 一类，避免 θ） |
| `crossbar` | `crossbar(x0, x1, y, *, thick, name, ends="slot")` | 厚度 = `thick`；两端可声明端点槽或与干 overlap |
| `diagonal_pair` | `diagonal_pair(apex, left_foot, right_foot, *, weight, thin_ratio, crotch, ink_trap=0.0, compensate=True)` | 两条斜笔视觉粗细按角度补偿（复用 `optics.stem.diagonal_compensation`）；顶点内侧削薄到 `crotch`；可选墨阱深度 |
| `crossing` | `crossing(a0, a1, b0, b1, *, weight, compensate=True)` | x / X 一类交叉；交点区域不产生墨块堆积（以合并后面积的上限来测） |
| `spine` | `spine(top_terminal, bottom_terminal, *, thick, thin, tension, axis_deg)` | S 形脊中段厚度 = `thick`，两端渐细到 `thin`；两端是端点槽 |
| `hook` | `hook(stem_face_x, y_join, tip, *, thick, thin, depth, tension)` | 包装 `construct.hook`，并让它带上厚度：钩内外两条边 + 端点槽 |
| `tail` / `ear` / `spur` | 同理 | 各自的端点槽与连接切线契约 |
| `dot` | `dot(center, diameter, *, shape="round"\|"square", overshoot=0.0)` | 圆点是超椭圆；与笔画的视觉大小关系由项目决定 |
| `drop` | `drop(top, bottom, *, width, tail_curve)` | 逗号 / 引号的泪滴形，单轮廓 |

### 4.4 `Measure`（加到 `draw.Drawing`）

```python
@dataclass(frozen=True, slots=True)
class Measure:
    kind: Literal["stem", "thin", "gap", "height", "crotch"]
    a: str                    # 标签
    b: str | None = None      # 标签；height 类只需 a
    expected: float | None = None
    direction_deg: float | None = None   # 斜笔的笔向；None = 水平测量

@dataclass(frozen=True, slots=True)
class Drawing:
    ...
    measures: tuple[Measure, ...] = ()   # 叠加（+）时合并；tagged() 时同步加前缀；不进 signature()
```

诊断直接读取构件声明的 `Measure` 来量竖干、细笔画、开口和削薄，取代现在 `AUDIT_STEMS`
加字母表的猜测机制。

### 4.5 笔构件 `anatomy.pen`

两个斜体 starter 里重复的 `slanted_polyline`、`stroke`、`pen_for_optical_stem`、`bowl`、
`open_bowl`、`nest_bowl`、`pen_dot`、`flourish_*` 收进 `anatomy.pen`，统一接收**三次骨架**
（`Fragment` 或 `CubicCenterline`），不再接收折线点列。曲线感知笔偏移（已确认的 D3）在这里落地。

---

## 5. 数值表、形态标记与度量

### 5.1 `System` 瘦身

`System` 只放全局数值：`upm`、`zones`、`overshoot`、`stem`、`slant`，以及**全局** token
（如 `shoulder_tension`、`bowl_exponent`、控制字宽 `n_width` / `o_width` / `H_width` / `O_width`）。

- 逐字宽度（`<glyph>_width`）由字形代码按控制字推导（设计师就是这么做的：`h = n`，`m ≈ 2n − stem`），
  或写成项目 `elements.py` 里的常量。
- 逐字步进（`<glyph>_advance`）删除，advance 只有一个来源：度量（§5.3）。
- 诊断加一条 System lint：token 名匹配 `^<字形名>_(width|advance)$` 时给出 warn，提示迁移。

### 5.2 `Zones` 可扩展

```python
@dataclass(frozen=True, slots=True)
class Zones:
    base: float = 0.0
    x: float; cap: float; asc: float; desc: float
    extra: Mapping[str, float] = {}     # 其他文字系统或项目自定义的区线，如 "smcp"、"cyr_x"
```

诊断用 traits（§5.4）决定某个字形对哪条区线负责，不再按字母名。

### 5.3 度量引擎 `typekernel.metrics`（新，从三个 starter 的 `spacing.py` 中抽出）

```python
Side = Abs | Stem | Token | Ref | Mirror | Optical

@dataclass(frozen=True, slots=True)
class Abs:    value: float
@dataclass(frozen=True, slots=True)
class Stem:   key: str; factor: float
@dataclass(frozen=True, slots=True)
class Token:  key: str; factor: float = 1.0
@dataclass(frozen=True, slots=True)
class Ref:    glyph: str; side: Literal["lsb", "rsb"]; delta: float = 0.0
@dataclass(frozen=True, slots=True)
class Mirror: pass                      # rsb = 本字的 lsb
@dataclass(frozen=True, slots=True)
class Optical:                          # 按光学留白匹配参照字形的同侧
    ref: str; side: Literal["lsb", "rsb"]; band: tuple[float, float] | None = None

@dataclass(frozen=True, slots=True)
class Metrics:
    keys: Mapping[str, tuple[Side, Side]]
    space: Side = Token("space_advance")
    pack: Literal["bbox", "slant-mid-x"] | None = None   # None = 按 System.slant 自动选

def resolve(metrics: Metrics, system: System, glyphs: Mapping[str, Glyph]) -> Mapping[str, tuple[float, float]]
def pack(glyph: Glyph, lsb: float, rsb: float, system: System, *, policy: str) -> Glyph

@dataclass(frozen=True, slots=True)
class Kerning:
    classes: Sequence[KernClass] = ()
    pairs: Sequence[KernPair | ClassKernPair] = ()
    exceptions: Sequence[KernPair] = ()
```

规则：

- 引擎字母无关；`keys` 里的字形名是项目数据。
- 按依赖顺序解析，检测循环引用；每个母版用自己的 `System` 分别解析。
- 没有 key 的字形不再静默退回 bbox：诊断报 `unspaced`，构建时用 `Stem("<默认>", 0.5)` 兜底，但兜底会写进 manifest。
- kerning 只用于明确的字偶。自动建议（§7.2 E 类）写到建议文件里，不自动生效。

### 5.4 形态标记 `traits`（字母无关的分类）

内核认识的 trait 词表（封闭，增改要进本节）：

| trait | 含义 | 被谁使用 |
| --- | --- | --- |
| `x-height` / `cap` / `ascender` / `descender` / `smcp` | 字形负责的垂直区间 | 区线贴合、超调检查 |
| `round-top` / `round-bottom` / `flat-top` / `flat-bottom` / `pointed-top` / `pointed-bottom` | 区线处的端形 | 超调检查 |
| `diagonal` | 主笔是斜笔 | 斜笔测量 |
| `mark` / `spacing-mark` | 组合用附加符 | advance 为 0、锚点检查 |
| `figure` / `tabular` | 数字 / 等宽 | 等宽检查 |
| `punct` / `symbol` | 标点 / 符号 | 灰度分组 |
| `no-stem` | 没有竖干（不做竖干测量） | 竖干检查 |

starter 的期望表和 traits 默认值都是数据（例如 latin-sans 的 `expect.py` 把 `o` 标成
`x-height, round-top, round-bottom`），拷进项目后由项目维护。

---

## 6. 感知
> **P2 已落地**：实现以 `typekernel.perceive` / `diagnose` / `review` 与 `ARCHITECTURE.md`「P2 落地摘要」为准；本节保留为契约原文，待下轮精简并入 ARCHITECTURE 后删除。
 `typekernel.perceive`（新，吸收 `qa.proof` / `qa.specimen_png`）

### 6.1 两条渲染路径

| 路径 | 输入 | 用途 | 依赖 |
| --- | --- | --- | --- |
| **live** | `GlyphDraft` / `Glyph`（不编译） | 编辑视图、上下文、叠图、diff，迭代时用 | Pillow + skia-pathops（先 simplify 成非零绕向，再以 even-odd 填充） |
| **shipped** | 编译后的 OTF / TTF / VF | 最终样张：kerning、特性、hinting、小字号 | Pillow（可选 raqm）；特性样张用可选的 uharfbuzz |

### 6.2 视图（`tk see` / `tk proof`）

| 视图 | 内容 | 命令 |
| --- | --- | --- |
| 编辑视图 | 浅色填充 + 轮廓线 + 节点（方 = 角点，圆 = 平滑）+ 控制柄 + 节点标签 + 槽位标记 + 区线与超调带 + 侧距与步进 + `Measure` 实测值标注 | `tk see n [--masters]` |
| 上下文 | `nn?nn oo?oo HH?HH OO?OO`（按 trait 选择参照），3 个字号 | `tk see n --context` |
| 母版叠图 | 各母版叠放，对应节点之间连线（看插值路径是否交叉） | `tk see n --overlay masters` |
| 前后对比 | 与快照对比：红 = 删除，绿 = 新增 | `tk see n --diff [snapshot]` |
| 参照并置 | 与一款参照字体并排显示（只看不测，遵守已确认的 D4） | `tk see n --reference ref.otf` |
| 文本 | 瀑布（含 9–16 px 小字号）、段落、间距串、字偶串、字符网格、按名字形网格（含未编码字形） | `tk proof …` |
| 灰度 | 段落模糊后的灰度热图，暴露黑度不均 | `tk proof color` |

每张 PNG 都配一个同名 `.json` 边车文件：视图类型、字形列表、各字形轮廓哈希、母版、渲染参数、
图中标注的测量值。agent 用 JSON 对照图片，不必从像素里猜数字。

### 6.3 测量 `tk explain`

```python
def explain(session: ProjectSession, glyph: str, *, master: str | None = None) -> GlyphReport
```

`tk explain n --json` 输出：bbox、advance、lsb / rsb（及其来自哪条 metrics key）、节点表
（坐标、标签、平滑或角点、接合角）、槽位与填充结果、`Measure` 实测值与期望值、字腔数和面积、
墨块数、开口宽度、区线贴合与超调实测、墨量密度、`GlyphDraft.note`。

---

## 7. 诊断
> **P2 已落地**：实现以 `typekernel.perceive` / `diagnose` / `review` 与 `ARCHITECTURE.md`「P2 落地摘要」为准；本节保留为契约原文，待下轮精简并入 ARCHITECTURE 后删除。
 `typekernel.diagnose`（新，吸收 `cli/audit.py` 的逻辑）

### 7.1 协议 v2

```python
Scope = Literal["glyph", "pair", "font", "family"]
Level = Literal["error", "warn", "info"]

@dataclass(frozen=True, slots=True)
class Finding:
    check: str                 # 稳定 id，如 "topology.counters"
    level: Level
    glyph: str | None
    master: str | None
    where: str | None          # 标签或 "x,y"
    measured: float | str | None
    expected: float | str | None
    message: str
    hint: str = ""             # 「改什么」：指向构件参数或标签

class Check(Protocol):
    id: str
    scope: Scope
    def run(self, ctx: CheckContext) -> Iterable[Finding]: ...
```

- 输出人读文本和 `--json`；`--masters all` 对每个母版都跑一遍。
- **基线**：`audit-baseline.json` 记录被接受的 warn，每条必须写 `reason`；基线中的条目对应的字形
  哈希变化后，该条自动失效。不允许接受 error。
- 退出码：有 error 时为 1；`--strict` 下 warn 也算失败。

### 7.2 检查目录（全部字母无关，由 traits / expect / 标签驱动）

| 类 | 检查 | 默认级别 |
| --- | --- | --- |
| A 结构 | 轮廓方向、开放轮廓、自交（pathops）、零长段、重复节点、母版签名兼容 + `fontTools.varLib.interpolatable`、组件缺失或循环、unicode 重复、组合字锚点缺失、charset 缺字 | error |
| B 拓扑 | 闭合字腔数 vs `expect.counters`；墨块数 vs `expect.islands`；细缝字腔（面积 < k·stem²，常见于 overlap 接合）；开口宽度（`aperture.*` 标签） | warn（项目可升级为 error） |
| C 垂直度量 | flat-* 端贴合区线（容差 1）；round-* 端超调落在 `[0.5, 1.5] × overshoot`；pointed-* 同理；`expect.reach` 要求触及的区线 | warn |
| D 笔画 | `Measure` 实测 vs 期望 / `System.stem`；斜笔补偿；同组细横笔一致性；削薄点厚度 | warn |
| E 间距 | 墨溢出 advance；无 key 字形；字偶碰撞（全部 kerning 字偶 + 样张串里的相邻字偶，按 kerning 后的最小墨距）；引用一致性（`Ref` 引用的两侧光学留白相差过大）；kerning 极值 | warn |
| F 灰度 | 每个字形的墨量密度 vs 同 trait 组中位数（z 分数 > 2 报出） | info → warn |
| G 插值 | 在 t = 0.25 / 0.5 / 0.75 处插值出实例，检查自交和拓扑期望；字干随 wght 单调变化 | warn |
| H 发布 | 垂直度量、name 表、OS/2 字重类、STAT、字形名合法性；可选调用 FontBakery / fontspector | `tk check --release` 专用 |
| I 意图 | Intent 区间（现有）；System lint（§5.1） | warn |
| J 评审 | 字形哈希相对上一次评审已变化 → stale | info（发布时为 error） |

### 7.3 期望表 `Expect`

```python
@dataclass(frozen=True, slots=True)
class Expect:
    counters: int | None = None        # 闭合字腔数（不计细缝）
    islands: int | None = None         # 墨块数（i = 2，colon = 2）
    apertures: int | None = None       # 开口数（按 aperture.* 标签计数）
    reach: tuple[str, ...] = ()        # 必须触及的区线名：("base", "x") / ("base", "asc") / ("desc", "x")
```

期望表是项目数据（starter 带一份 `expect.py`）。为了防止「改期望表来通过检查」：
`tk audit` 会列出项目期望表相对 starter 原始表的改动，评审时必须对每处改动写理由（§8）。

### 7.4 拓扑的计算方法

在 live 路径上：对最终轮廓（槽位填充之后）做 `pathops.simplify`（非零绕向），得到不重叠的
外轮廓和洞。洞的数量减去细缝即字腔数；外轮廓数即墨块数。开口不做通用检测，只认构件产生的
`aperture.*` 标签，避免启发式误报。

---

## 8. 评审
> **P2 已落地**：实现以 `typekernel.perceive` / `diagnose` / `review` 与 `ARCHITECTURE.md`「P2 落地摘要」为准；本节保留为契约原文，待下轮精简并入 ARCHITECTURE 后删除。
 `typekernel.review`（新，吸收 `qa.gates`）

### 8.1 评审记录

```json
{
  "group": "lc.n",
  "round": 3,
  "reviewer": "agent:<model>",
  "verdict": "fail",
  "masters": ["Regular", "Bold"],
  "glyphs": {"n": "<outline_hash>", "h": "<outline_hash>"},
  "proofs": ["proofs/r3/see-n.png", "proofs/r3/context-n.png"],
  "expect_changes": [],
  "notes": "肩接干太高，冠点偏左；下一轮把 join_depth 从 0.18 提到 0.24 × x",
  "date": "2026-11-02"
}
```

- `tk review open <group>`：生成该组的标准视图，在 `reviews/` 里写一份 `verdict: pending` 的模板。
- `tk review record <group> --verdict pass|fail --note "…"`：写入记录，并自动填好当前哈希。
- **过期**：只要组内任一字形的哈希和最新的 pass 记录不一致，该组就是 stale。
- **两级门**：`reviewer` 以 `agent:` 开头的记录是组级的推进门（agent 可以写）；里程碑和发布要求
  `approvals/` 里由人写的批准（`approver` 以 `human:` 开头）。工具拒绝替人写 `approved: true`。

### 8.2 `tk status`（设计师的任务板）

```
Trial  (latin-sans v2)          charset 312/330  masters 3  compat ok
group        glyphs  E  W  review          masters
lc.n         8/8     0  1  pass r3         ok
lc.o         7/7     0  0  stale (o,e)     ok
lc.mixed     4/6     0  3  fail r2         -
uc.straight  0/6     -  -  -               -
…
release gate: blocked (2 groups not passed, 0 human approvals)
```

---

## 9. 槽位与插件 v2

### 9.1 站点信息补全

```python
@dataclass(frozen=True, slots=True)
class CornerSite:
    tag: str
    point: Point
    in_dir: Point; out_dir: Point
    in_len: float; out_len: float
    in_kind: Literal["line", "curve"]      # 新
    out_kind: Literal["line", "curve"]     # 新
    exterior: Point                        # 新：外侧单位法向
    stem: float | None                     # 新：来自构件的 Measure
    zone: str | None                       # 新：角点所在区线名（容差内）
    role: ContourRole
    meta: Mapping[str, float]
    def point_in(self, trim: float) -> Point    # 新：沿真实进入边（含曲线）回退 trim 后的点
    def point_out(self, trim: float) -> Point   # 新：沿真实离开边前进 trim 后的点
```

`EndSite` 同样补上 `stroke_width`、`stroke_dir`、`a_kind` / `b_kind`、`point_a(trim)` / `point_b(trim)`。

### 9.2 填充契约 v2

- 填充器必须用 `point_in` / `point_out` 求路径端点。现在 slab 用 `point − in_dir × trim`，
  在曲线邻边上落不到轮廓上，这正是 build 报错的原因。
- 填充器可以声明 `requires = {"line-line"}`；条件不满足时，`apply_slots` 跳过并记一条 info，
  不抛异常，也不画出歪掉的几何。
- 填充失败统一抛 `SlotFillError(glyph, tag, reason)`。
- **语义契约测试**（每个插件都要有，用合成站点）：

| 插件 | 语义断言 |
| --- | --- |
| `slab(length, thickness)` | 在脚点处，墨沿区线方向、朝竖干外侧伸出 `length × stem`（±1），衬线厚度（垂直于区线）= `thickness × stem`（±1）；衬线底边与区线重合，不是斜向凸块 |
| `bracketed` | 衬线与干之间的托架 G1 连续，托架高度符合参数 |
| `rounded(radius)` | 圆角半径实测 = radius（±0.5） |
| `wedge` / `ink_trap` | 楔角 / 墨阱深度实测 = 参数 |
| `angled(deg)` 端 | 切口相对笔画法向的角度 = deg（±0.5°） |
| `ball` / `flare` 端 | 球径 / 外扩量实测 = 参数 |

### 9.3 覆盖率要求

用 `anatomy.stem` / `crossbar` / `open_bowl` 等构件画出来的字，脚、顶、端点都会自动声明槽位。
starter 的验收包括一条 litmus 测试：latin-sans 把 `corners` 换成 `slab` 之后，所有
`stem.*.foot.*` 和 `stem.*.top.*` 槽位上都能测到衬线（按 slab 的语义断言），build 成功，
`tk audit` 0 error。

---

## 10. 轴、母版、实例与家族

```python
@dataclass(frozen=True, slots=True)
class Axis:
    tag: str                    # "wght" / "wdth" / "opsz" / "ital" / 自定义
    name: str
    minimum: float; default: float; maximum: float
    map: Sequence[tuple[float, float]] = ()   # 用户坐标 → 设计坐标（avar）
    labels: Mapping[float, str] = {}          # STAT 标签：{100: "Thin", 400: "Regular", …}

@dataclass(frozen=True, slots=True)
class MasterSpec:
    name: str
    location: Mapping[str, float]   # 设计坐标
    system: System

@dataclass(frozen=True, slots=True)
class Instance:
    name: str
    location: Mapping[str, float]   # 用户坐标
    style_map: tuple[str, str] | None = None   # (family, style) 的 RIBBI 链接
```

- 构建产出 designspace 5（含轴、母版、实例、STAT 标签）；VF 走 fontmake / varLib。
- 静态实例：默认用 `varLib.instancer` 从 VF 切出，保证静态版与 VF 一致；也可以从 designspace 逐个实例构建。
- **designed deltas**：母版之间允许不同的 `System`（干宽、控制字宽、接干深度、开口），以及
  `@fn.master` 覆盖画法；诊断 G 类负责插值质量。
- **家族**：家族根目录放 `family.py`，`FAMILY = Family(name, members=(Member("upright/", ital=0), Member("italic/", ital=1)))`；
  `tk build --family` 产出共享 STAT 的直体 / 斜体 VF（或带 `ital` 轴的单个 VF）。Oblique 只能以 Oblique 的名义出现（沿用 `compile.oblique`）。

---

## 11. 特性 `typekernel.features`（新）

### 11.1 命名后缀语法 → 自动特性（字母无关）

| 命名 | 生成 |
| --- | --- |
| `<base>.ssNN` | `ssNN` 替换；`aalt` 收录 |
| `<base>.cvNN` | `cvNN` 替换 |
| `<base>.sc` | `smcp`；`<BASE>.sc` 对应 `c2sc` |
| `<base>.case` | `case` |
| `<base>.tf` / `.lf` / `.osf` / `.tosf` | `tnum` / `lnum` / `onum` 的组合规则 |
| `<a>_<b>[_<c>]` | `liga`（有 `.dlig` 后缀则进 `dlig`） |
| `<base>.alt` / `.altN` | `salt` / `aalt` |
| 组合字锚点、kerning 分组 | 交给 ufo2ft 的 kern / mark / mkmk / GDEF 特性写入器 |

### 11.2 手写特性

`features/*.fea` 按文件名顺序拼接在自动特性之后；可以用 `# tk:replace <feature>` 声明「整个替换某个自动特性」。
用 feaLib 做语法检查，失败时报 `features.syntax` error，带文件名和行号。

### 11.3 带特性的样张

`tk proof --text "…" --features ss01,onum` 需要 HarfBuzz（可选 extra，通过 uharfbuzz 塑形后再按字形 id 渲染）。

---

## 12. 编译与发布

- 垂直度量策略：`VerticalMetrics.from_zones(system, policy="typo-equals-win")`，可在 `Project` 中覆盖。
- name / OS/2：由 `FamilyInfo`、`Instance` 自动生成（usWeightClass、fsSelection、RIBBI 链接）。
- Hinting（可选）：TTF 用 ttfautohint，CFF 用 otfautohint；manifest 记录是否 hinting 以及工具版本。
- `--resolve-overlaps` 只用于静态构建（沿用）。
- `tk check --release`：诊断 H 类 + 可选 FontBakery profile；结果写进 manifest。

---

## 13. 与文字系统无关

- 内核里没有任何拉丁专有的列表或分支。拉丁知识（字符集、组合表、metrics keys、期望表、样张串、
  traits 默认值）全部在 starter pack 里。
- `Zones.extra` 和 traits 词表是扩展点；以后做西里尔 / 希腊字母时，加 starter pack 和必要的 trait，不改检查逻辑。
- 中日韩等方块字不在本期范围内，但不能留下阻碍：区线、度量、拓扑检查都不能假设拉丁比例。

---

## 14. 架构守卫 v2

在现有 7 条之外新增（都用 `ast` 实现，不加依赖）：

1. **字形名字面量**：内核包（`geo draw anatomy system project metrics axes features font perceive diagnose review compile cli plugins`）
   的字符串字面量里，不得出现单字母或 AGL 字形名，也不得出现由它们组成的集合（测试夹具除外）。
2. **分层 DAG**：按 §2 的依赖规则检查 import 方向。
3. **构件不组字**：`anatomy` 里的公开函数只能返回 `Drawing` 或构件 dataclass；函数名不得包含字形名，也不得以 `glyph_` / `build_` 开头。
4. **文档如实**：被 git 跟踪的 Markdown（含 skills）里引用的仓库路径必须存在且没有被 gitignore；
   出现的 `typekernel.x.y` 符号必须能 import。
5. **starter litmus**（放在 `tests/starters/`）：期望表全部满足；`tk audit` 0 error；slab 切换的语义测试通过；
   样张感知哈希与 `reviews/` 里最新 pass 记录一致（视觉回归，更新必须伴随评审记录）。

---

## 15. 公开 API 增量一览

| 模块 | 新增公开符号 |
| --- | --- |
| `draw` | `Measure`；`Drawing.measures`；`CornerSite` / `EndSite` 新字段与 `point_in` / `point_out` 等 |
| `anatomy` | `stem` `arch` `bowl` `bowl_join` `open_bowl` `BarSpec` `crossbar` `diagonal_pair` `crossing` `spine` `hook` `tail` `ear` `spur` `dot` `drop`；`anatomy.pen.*` |
| `system` | `Zones.extra`；trait 词表常量 `TRAITS` |
| `project` | `Project`（清单形态）`FamilyInfo` `Charset` `Composite` `compose` `GlyphDraft` `ComponentRef` `open_project` `ProjectSession` `GlyphBuildError` |
| `metrics` | `Abs` `Stem` `Token` `Ref` `Mirror` `Optical` `Metrics` `Kerning` `resolve` `pack` |
| `axes` | `Axis` `MasterSpec` `Instance` `Family` `Member` |
| `features` | `Features` `generate_features` |
| `perceive` | `render_live` `edit_view` `context_view` `overlay_view` `diff_view` `explain` `GlyphReport`；文本样张函数（迁自 `qa.proof`） |
| `diagnose` | `Check` `CheckContext` `Finding` `Expect` `AuditConfig` `run_audit` `Baseline` |
| `review` | `ReviewRecord` `ReviewPolicy` `open_review` `record_review` `status` |
| `cli` | `tk see` `tk explain` `tk status` `tk review` `tk check`；`tk audit --json/--masters/--strict` |

## 16. 删除清单（落地时直接删，不留双轨）

- `System.tokens` 中的 `<glyph>_advance` 路径、`Project.default_advance`、bbox advance 的静默兜底。
- `system.py` 中的模块级约定：`FAMILY_NAME` `STYLE_NAME` `MASTER_LOCATIONS` `AUDIT_STEMS` `EXTRA_CHECKS`；
  `font.py` 中的 `get_project`；`spacing.py` 中的 `apply_spacing` 引擎代码。
- `cli/audit.py` 中的 `_DEFAULT_NON_VERTICAL` / `_DEFAULT_DIAGONAL`；`plugins/checks/zone.py` 中的字母集合。
- `cli/load.py` 中的 `_purge_project_local_modules` 和删除 `__pycache__` 的逻辑。
- 两个斜体 starter 里重复的笔工具函数（迁入 `anatomy.pen`）。

## 17. 设计禁令（在 `ARCHITECTURE.md` §9 的基础上增加）

7. `System` 里不放逐字数据。
8. 内核不出现字母列表，也不按字母名分支；需要分类时用 traits。
9. 解剖构件只产出结构件，不组装整字。
10. 评审记录不能自动生成 pass；agent 不能写人工批准。
11. 改期望表、基线或阈值，必须单独提交并写明理由。
