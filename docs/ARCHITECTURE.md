# typekernel 架构

> 第一性原理：**人类字体设计师怎么做，coding agent 用 typekernel 时就怎么做。**
> 库只提供“设计师的工具”，不提供“一副已经设计好的字”。

本文描述 typekernel 当前的架构与公开契约。实现与评审以本文为准。

目标架构草案见 [`docs/design/target-architecture.md`](design/target-architecture.md)；某一节落地后并入本文并从草案删除。

### 实现状态（诚实表）

| 项 | 状态 | 说明 |
| --- | --- | --- |
| `glyphs_italic/` 约定 | **未实现** | §2「母版与斜体」写的是另一套字形目录；现行斜体靠独立 starter（`latin-humanist-italic` / `latin-chancery`），没有同项目 `glyphs_italic/` 加载路径 |
| `plugins.spacing` | **空包** | 仅占位；现行间距是 `Project.metrics` + `typekernel.metrics`（数据仍可放在项目 `spacing.py`） |
| System token lint (`*_width`/`*_advance`) | **已落地** | 控制字 `n/o/H/O_width` 保留；其余迁到项目 `elements.WIDTHS` |
| `Drawing.measures` / `Measure` | **已落地** | `+` 合并、`tagged` 前缀、`mirrored_x` 保标签；不进 `signature()` |
| 标签语法 / `anatomy.tags` | **已落地** | §6.3.1；`tags.grammar` info 检查；不合规清单见 P3-1 测试 |
| Tracy / 光学间距插件 | **未接入工作流** | `optics` 有原语；Tracy 法与光学侧距插件未挂进 `tk audit` / 默认 spacing 路径 |
| 内核字母名 | **已清** | `cli/audit` / `checks.zone` / `checks.stem` 字母表已删；守卫扫 AGL / 单字母字面量；光学 stem 靠项目 `AUDIT_STEMS` |
| Starter 字形质量 | **未视觉批准** | 三套 starter 是结构示例，`tk audit` 可过，样张尚未通过人工视觉评审 |
| 槽位曲线邻边 | **已修** | `CornerSite.point_in/out`、`EndSite.point_a/b` 按弧长；角点填充器改用它们；`requires={"line-line"}` 时曲线邻边跳过；`Project.evaluate` 报 `glyph 'X' slot 'tag': …` |

---

## 1. 三层分离

```
┌─────────────────────────────────────────────────────────────────┐
│  字体项目（用户 / agent 拥有）   tk new myfont                   │
│  brief.md  system.py  elements.py  glyphs/*.py  spacing.py      │
│  masters.py  font.py  proofs/                                    │
│  ← starter 模板“拷贝进来”（shadcn 模式），之后完全归 agent 改     │
└───────────────────────────────▲─────────────────────────────────┘
                                │ 只调用公开 API
┌───────────────────────────────┴─────────────────────────────────┐
│  插件（可选、互相独立、按协议实现）                              │
│  corners: plain / rounded / slab / bracketed / wedge / ink_trap  │
│  ends:    flat / angled / ball / flare                           │
│  passes:  overshoot / diagonal_comp / crotch_thin /              │
│           compensated_weight                                     │
│  construct: skeleton_pen（broad_nib / pointed_pen）              │
│  spacing: 预留（现行路径是项目里的 spacing.py）                  │
│  checks:  direction/stem/zone/compat/overlap + EXTRA_CHECKS   │
└───────────────────────────────▲─────────────────────────────────┘
                                │ 只依赖内核
┌───────────────────────────────┴─────────────────────────────────┐
│  内核（没有任何字母名、没有任何风格枚举）                         │
│  L0 geo      三次曲线、片段、连续性、测量                         │
│  L1 draw     Writer：带命名节点 / 角点槽 / 端点槽的轮廓书写        │
│  L2 glyph    Drawing、Glyph、Project、Master                     │
│  L3 system   System 数值表（对齐区、stems、超调、项目自定义 token）│
│  L4 proof    渲染字串、叠图、测量报告                             │
│  L5 compile  UFO / designspace / fontTools                       │
│  CLI         tk new / tk proof / tk audit / tk build / tk diff   │
└─────────────────────────────────────────────────────────────────┘
```

依赖规则（`tests/architecture/test_boundaries.py` 在 CI 里强制）：

- 内核不 import 插件；插件之间不 import；项目只用公开符号。
- 内核源码里**不得出现字母命名的函数**（`*_from_n`、`build_H`、`n_yoke` 一类）和风格分支（`style.serif == ...`）。
- 插件不得 import 任何 `_` 私有符号。

---

## 2. 核心概念

### `System`：设计师的数值表

```python
# myfont/system.py
from typekernel.system import System, Zones, Overshoot

REGULAR = System(
    upm=1000,
    zones=Zones(base=0, x=520, cap=700, asc=740, desc=-210),
    overshoot=Overshoot(round=12, pointed=10),
    stem={"lc": 84, "lc_h": 70, "uc": 92, "uc_h": 76},
    tokens={"n_width": 430, "o_width": 470, "shoulder_tension": 0.58},
)
```

- 只是数据。所有派生关系（“x 高越大字怀越宽”）要么由设计师写成显式数值，要么写在**项目自己的** `elements.py` 里。
- `tokens` 开放给项目自定义，库不预设语义。
- 预设降级为 starter 模板里的一份 `system.py`。

### `Fragment`：可复用的路径片段

元素不是闭合实体，而是**开放路径片段**：有起点、终点、两端切线，可以被拼进任何轮廓。

```python
@dataclass(frozen=True)
class Fragment:
    segments: tuple[Segment, ...]       # 三次 / 直线
    nodes: tuple[Node, ...]             # 片段内的命名点（完整契约见 6.1）
    @property
    def start(self) -> Point: ...
    @property
    def end(self) -> Point: ...
    def start_tangent(self) -> Vec: ...
    def end_tangent(self) -> Vec: ...
```

内核提供**不含字母语义的几何构造器**：`tensioned_arc`、`superellipse_quarter`、`spring`（直线进曲线、可带削薄）、`diagonal_band`（带斜笔补偿）、`hook`。“肩”“碗”是用这些拼出来的，放在项目或 starter 里。

### `Writer`：设计师绕轮廓走一圈

```python
# myfont/glyphs/lower/n.py
from typekernel.draw import Writer
from typekernel.project import glyph
from myfont.elements import arch            # 项目自己的元素

@glyph("n", group="lc.straight")
def n(s):                                   # s: 当前母版的 System
    st, xh = s.stem["lc"], s.zones.x
    a = arch(s, left=st, counter=s.tokens["n_width"] - 2 * st)

    w = Writer()
    w.start((0, 0)).corner("stem.l.foot.o")
    w.line((0, xh)).corner("stem.l.top.o")
    w.line((st, xh)).node("stem.l.top.i")
    w.fragment(a.outer)                     # 肩外沿；切线由片段保证连续
    w.line((a.outer.end.x, 0)).corner("stem.r.foot.o")
    w.line((a.inner.start.x, 0)).corner("stem.r.foot.i")
    w.fragment(a.inner)                     # 字怀
    w.line((st, 0)).corner("stem.l.foot.i")
    return w.close().build()
```

- 每个点都可以命名（`node`），角点可以声明成**槽**（`corner`），笔画开口可以声明成**端点槽**（`end`）。
- 字形代码只决定**结构和数值**，不知道将来挂什么衬线 / 端点。
- `Writer` 在拼接时检查连续性（声明为平滑的连接必须 G1；可选 G2）。连接不顺就报错，不在事后补。

### 槽位插件：风格维度和字母解耦

```python
# myfont/font.py
from typekernel.project import Project
from typekernel.plugins.corners import slab, plain
from typekernel.plugins.ends import angled

project = Project(
    system=REGULAR,
    glyphs="glyphs/",
    corners={"*.foot.*": slab(length=0.42, thickness=0.18), "*": plain()},
    ends={"*": angled(deg=12)},
)
```

- 衬线插件只看到一个 `CornerSite`（角点位置、进出边方向、所在 stem 宽、标签），返回替换该角点的片段。
- 无衬线 → 衬线：**改 `font.py` 一行，0 个字形文件改动。**
- 某个字要例外（`r` 只要左脚衬线），在该字形里换标签或声明 `corner(..., fill="plain")`，不改插件。

### 构造方式也是插件，不是唯一真相

设计师的画法不止一种，三种都应支持：

| 构造方式 | 适用 | 说明 |
| --- | --- | --- |
| `contour`（默认） | 无衬线、几何、工整衬线 | `Writer` 绕外形一圈 + 字怀 |
| `overlap` | 很多设计师的日常做法 | stem、肩各画一块并允许重叠；**接合形状由各块自身形状设计**，静态导出时去除重叠，可变字体保留重叠 |
| `skeleton + pen` | 人文、手写、斜体 | 骨架 + 宽头 / 尖头笔模型生成轮廓（复用 `geo.stroke`） |

`overlap` 模式消掉了可变字体的一大类兼容问题：可变字体里重叠可以保留，母版之间只需要每块形状的点结构一致。

禁令只有一条：**不允许事后修缝。** 连接难看，就去改画这个连接的片段或形状。

### `Pass`：显式的光学修正

```python
@glyph("b", group="lc.bowl")
def b(s):
    d = draw_b(s)
    d = crotch_thin(d, at="bowl.join.top", amount=0.82)  # 这一刀改了什么，读代码就看得见
    return d
```

光学修正是**写在字形里、可读、可删**的函数调用，不藏在 builder 里。

### 母版与斜体

- 同一个字形函数用不同母版的 `System` 求值；兼容性靠节点标签 + 段结构检查。
- 某个母版需要不同画法时，用 `@n.master("Black")` 单独覆盖。
- 斜体是 `glyphs_italic/` 下的**另一套字形文件**（可以 import 正体的元素），不是开关。（**约定尚未实现**——见上表；现行用独立 italic starter。）

### 间距

- `metrics keys`（`Abs`/`Stem`/`Token`/`Ref`/`Mirror`；`Optical` 签名预留至 P2）：声明在 `Project.metrics`，引擎在 `typekernel.metrics`。
- Tracy 法、光学测量做成插件，可选。（**尚未接入工作流**——见上表；`plugins.spacing` 仍为空包。）
- 项目 `spacing.py` 只放 `METRICS` / `KERNING` 数据，agent 可以手调。

---

## 3. 标准工作流

```
tk new myfont --starter latin-sans      # 拷入 system/elements/控制字模板
1. 写 brief.md
2. 改 system.py（每个数值都要能说出理由）
3. 画控制字 n o H O              → tk proof control   → 看图，改，重复
4. 写 / 改 elements.py（肩、碗、弧）→ 扩字组           → tk proof lc.n / lc.o / diag
5. tk audit                         → 读 stem/zone 偏差，逐字修
6. 选衬线 / 端点插件（font.py）      → tk proof all
7. spacing.py                       → tk proof spacing / kern
8. 母版、斜体                        → tk audit --compat；tk proof ladder
9. tk build                         → OTF / TTF / VF
```

agent 的每一步都在**改自己项目里的代码**，看**自己生成的样张**，和设计师在 Glyphs 里的循环一一对应。

---

## 4. 验收方式

| 层 | 测什么 | 怎么测 | 出现字母名？ |
| --- | --- | --- | --- |
| 内核单测 | 几何契约：片段切线、拼接连续性、标签在变换后保留、测量精度、编译不改点 | 合成形状（矩形、圆环、合成弧） | **不允许** |
| 插件契约测试 | 每个插件对任意合法 `CornerSite` / `EndSite` 产出合法拓扑、方向正确、标签保留、跨母版结构稳定 | 合成角点 / 端点，属性测试 | **不允许** |
| 项目审计 `tk audit` | 设计师会量的东西：stem 实测 vs `System`、对齐区和超调、轮廓方向、母版兼容、侧距与 `n`/`o` 基准的偏差 | 按命名节点测量，输出报告 | 是，在**用户项目**里 |
| 样张 `tk proof` | 设计师会看的东西：控制串、字组串、间距串、字偶串、多字号瀑布、母版叠图、前后对比 | PNG + 视觉 agent / 人工审阅 | 是，在**用户项目**里 |

审计是**诊断**，不是美学上的通过 / 失败门禁。只有结构性错误（方向、自交、母版不兼容）才算硬失败；stem / zone 偏差是修改清单。字形质量由视觉审阅决定，不用数值门禁冒充。

默认样张串（starter 内置，项目可改）：

```
control:  nnonoo  nnhnnhnn  oobobboo  HHOHOO  HOHHOO
lc.n:     nnnmnnnhnnnrnnnunnn
lc.o:     ooobooodoooppooqooo  oocooeoo
diag:     vvwvxvyv  nvnwnxnyn
spacing:  hamburgefonstiv  Hamburgefonstiv  HAMBURGEFONSTIV
kern:     AV Ta To Yo LT P. F,  "ry" "f."
```

---

## 5. 包布局

```
src/typekernel/
  geo/                 # 三次曲线、片段、连续性、测量
  draw/
    __init__.py        # 公开：Fragment, Writer, Drawing, ContourRole, Node, Slot
    fragment.py        # Fragment + 变换
    writer.py          # Writer
    drawing.py         # Drawing、标签查询、槽位清单、兼容签名
    construct.py       # 不含字母语义的几何构造器
    slots.py           # CornerSite / EndSite / 填充协议 / 槽位应用
  system/
    __init__.py        # 公开：System, Zones, Overshoot, Intent/Brief
    table.py           # System / Zones / Overshoot
    intent.py          # Brief → System 映射与 check_intent
  project/
    __init__.py        # 公开：Project, glyph, Master
    registry.py        # @glyph 发现与注册
    evaluate.py        # 按母版求值 → Drawing → font.Glyph
  plugins/
    corners/  ends/  passes/  spacing/  checks/  construct/
  cli/
    __main__.py        # tk new / proof / audit / build / diff
  starters/
    latin_sans/              # tk new --starter latin-sans
    latin_humanist_italic/   # tk new --starter latin-humanist-italic
    latin_chancery/          # tk new --starter latin-chancery
```

`draw` / `system` / `project` / `cli` 是内核；`plugins` 是插件；`starters` 是模板数据，**不被任何内核模块 import**。

---

## 6. 交接规格

本节是可以直接照着写代码的契约。签名是规范性的；内部实现自由。与第 2 节的示意代码冲突时，以本节为准。

### 6.1 `draw.Fragment`

```python
Segment = LineSegment | CubicSegment          # 复用 geo.segment

@dataclass(frozen=True, slots=True)
class Node:
    index: int                # 在片段 / 轮廓中的 on-curve 序号（0 = 起点）
    tag: str                  # 点分命名，如 "stem.l.foot.o"
    meta: Mapping[str, float] # 可选：stem 宽等给插件读的提示

@dataclass(frozen=True, slots=True)
class Fragment:
    segments: tuple[Segment, ...]             # 首尾相接，非空
    nodes: tuple[Node, ...] = ()              # 片段内的命名点（可选）

    start: Point;  end: Point                 # property
    def start_tangent(self) -> Point: ...     # 单位向量
    def end_tangent(self) -> Point: ...
    def reversed(self) -> Fragment: ...       # 方向反转，节点 index 重映射
    def translated(self, dx: float, dy: float = 0.0) -> Fragment: ...
    def mirrored_x(self, axis_x: float) -> Fragment: ...   # 镜像并反转方向，保持绕向语义
    def mirrored_y(self, axis_y: float) -> Fragment: ...
    def tagged(self, prefix: str) -> Fragment: ...         # 给所有节点 tag 加前缀
```

规则：

- 构造时校验首尾相接（精确相等或 `1e-9` 内），否则 `ValueError`。
- 片段内部相邻段之间，若任一侧是曲线，必须 G1（复用 `geo.smoothness.g1_join_error`，容差 `1e-6`），除非该节点 `meta` 含 `cusp=1`。
- 不引入任何坐标采样；所有变换都作用在控制点上。

### 6.2 `draw.Writer`

```python
class Writer:
    def start(self, p: PointLike) -> Writer
    def line(self, p: PointLike) -> Writer
    def curve(self, c1: PointLike, c2: PointLike, p: PointLike) -> Writer
    def fragment(self, f: Fragment, *, prefix: str = "") -> Writer
        # f.start 必须等于当前点；否则 ValueError（不自动连线）
    def node(self, tag: str, **meta: float) -> Writer       # 给“当前点”命名
    def corner(self, tag: str, **meta: float) -> Writer     # 当前点 = 角点槽（允许不连续）
    def cusp(self) -> Writer                                 # 当前点允许切线不连续，但不是槽
    def end(self, tag: str, **meta: float) -> Writer        # 下一段 = 端点槽（笔画切口）
    def close(self, role: ContourRole = "ink") -> Writer    # 闭合当前轮廓，可继续 start 下一个
    def build(self) -> Drawing
```

语义：

1. **连续性在书写时检查，不在事后修。** `close()` 和 `build()` 时检查每个 on-curve 节点：若相邻两段至少一段是曲线，则必须 G1；被 `corner()` / `cusp()` 标记的节点除外。失败抛 `ContinuityError`，信息里带节点 tag 或坐标、实测角度。
2. **两段都是直线的节点**默认允许转角，不需要声明。
3. `role="ink"` 的轮廓在 `build()` 时规范为逆时针，`"counter"` 规范为顺时针（与 `geo.signed_area` 的符号约定一致——正为逆时针，方向反转时节点 index 同步重映射）。
4. 同一 `Drawing` 内 tag 必须唯一；重复抛 `ValueError`。
5. `Writer` 不知道任何字母、风格或 `System`。

### 6.3 `draw.Drawing`

```python
ContourRole = Literal["ink", "counter"]

@dataclass(frozen=True, slots=True)
class Slot:
    kind: Literal["corner", "end"]
    tag: str
    contour: int
    node: int                 # corner：角点 index；end：切口段起点 index
    meta: Mapping[str, float]
    fill: str | None = None   # 字形内显式指定的填充名，覆盖项目配置

@dataclass(frozen=True, slots=True)
class Drawing:
    contours: tuple[Contour, ...]
    roles: tuple[ContourRole, ...]
    nodes: tuple[tuple[Node, ...], ...]       # 每个轮廓的命名点
    slots: tuple[Slot, ...]

    def point(self, tag: str) -> Point
    def find(self, pattern: str) -> list[Node]          # fnmatch 风格匹配点分 tag
    def outline(self) -> Outline                        # 交给 compile / optics
    def signature(self) -> tuple                         # 兼容签名：每轮廓 (role, 段类型序列, tag 序列)
    def __add__(self, other: Drawing) -> Drawing         # 叠加（overlap 构造）；tag 冲突报错
    def translated(...); def mirrored_x(...)             # 同 Fragment
```

两个母版的 `signature()` 相等，就说明它们**结构可插值**（`signature()` 只做结构比较；插值检查由 `axes.interpolatable` 负责）。


### 6.3.1 标签语法（规范性）

解剖构件与诊断共用同一套节点 / 槽位标签语法（由 `typekernel.anatomy.tags` 解析；
诊断 `tags.grammar` 以 **info** 报告不合规标签）：

```
tag      := part ( "." qualifier )*
part     := stem | arch | bowl | join | bar | diag | spine | hook | tail | ear
          | spur | cross | dot | drop | aperture | serif | mark
qualifier:= side | position | face | endpoint | index
side     := l | r | t | b
position := foot | top | crown | apex | vertex | crotch | entry | exit | stress
face     := o | i             # 外侧 / 内侧
endpoint:= a | b             # 开口端点（仅 aperture）
index    := [0-9]+
```

例：`stem.l.foot.o`、`arch.crown.o`、`join.crotch.r`、`aperture.0.a`。

诊断约定：`stem.*.foot.o` 与 `stem.*.foot.i` 之间是竖干宽度；`join.crotch.*` 是削薄点；
`aperture.N.a` 与 `aperture.N.b` 之间是开口宽度。新增 part 名必须先写入本节并更新解析器。

### 6.4 槽位与填充协议（`draw.slots`）

```python
@dataclass(frozen=True, slots=True)
class CornerSite:
    tag: str
    point: Point
    in_dir: Point             # 进入角点的单位方向
    out_dir: Point            # 离开角点的单位方向
    in_len: float             # 进入边可裁剪的最大长度
    out_len: float
    role: ContourRole
    meta: Mapping[str, float]

@dataclass(frozen=True, slots=True)
class CornerFill:
    trim_in: float            # 从角点沿进入边回退的距离
    trim_out: float           # 沿离开边前进的距离
    path: Fragment | None = None  # 替换路径；None + 零 trim = 几何 no-op（≡ plain / 未匹配）

class CornerFiller(Protocol):
    def __call__(self, site: CornerSite, system: System) -> CornerFill: ...

@dataclass(frozen=True, slots=True)
class EndSite:
    tag: str
    a: Point; b: Point        # 切口段两端（按轮廓方向）
    a_dir: Point              # 到达 a 的笔画边方向
    b_dir: Point              # 离开 b 的笔画边方向
    role: ContourRole
    meta: Mapping[str, float]

@dataclass(frozen=True, slots=True)
class EndFill:
    trim_a: float; trim_b: float
    path: Fragment | None = None  # None + 零 trim = 几何 no-op（≡ 未匹配；退化参数同）

class EndFiller(Protocol):
    def __call__(self, site: EndSite, system: System) -> EndFill: ...

def apply_slots(
    d: Drawing,
    system: System,
    corners: Mapping[str, CornerFiller],   # 键是 tag 模式，按插入顺序首个匹配生效
    ends: Mapping[str, EndFiller],
    named: Mapping[str, CornerFiller | EndFiller] | None = None,  # 供 Slot.fill 显式引用
) -> Drawing
```

规则：

- 未匹配任何模式的槽保持原样（等价于 `plain`）。显式 `plain()` 与退化参数（如 `rounded(radius=0)`、`ball(radius=0)`、`flare(amount=0, depth=0)`、`angled(deg=0)`、`flat(inset=0)`）必须走同一 no-op：`trim=0` 且 `path=None`，不插入零长段、不消费角点/端点槽。
- 填充后的轮廓仍要通过 6.2 的连续性检查；插件产生不连续视为插件 bug。零长段不得靠 post-fill「跳过」蒙混——故意保留的切线不连续只走角点槽豁免；line–line 接合不要求 G1。
- 填充是**确定性**的：同一 `System` 结构下，不同母版填充出的段类型序列必须相同（插件契约测试覆盖）。
- `trim_in > in_len` 或路径首尾不落在裁剪点上 → `SlotFillError`。

### 6.5 构造插件 `plugins.construct`

字母无关。项目提供骨架，插件只负责笔模型展开为 `Drawing`：

```python
def broad_nib(thickness: float, *, contrast: float = 0.55, angle_deg: float = 30.0) -> Pen
def pointed_pen(thickness: float, *, contrast: float = 1.0, angle_deg: float = 0.0) -> Pen
def expand_skeleton(centerline, pen, *, join="round", cap="round", miter_limit=4.0, chord_budget=None) -> Drawing
    # closed + join="round" → ValueError (VF signature flip); use bevel/miter
    # chord_budget=None validates closed sampling; "auto"|float densifies (centerline-stable)
def expand_skeleton_cubic(centerline, pen, *, join="round", cap="round", ...) -> tuple[Drawing, CenterlineExpandReport]
```

规则：

- 复用 `geo.stroke.Pen` / `Centerline` / `CubicCenterline` / `expand` / `expand_cubic`；不 import starter，不出现字母名。
- 展开结果去掉近零长线段，并把剩余 `line` 提升为共线 handle 的 `cubic`（闭骨架禁止 `join="round"`（工具直接报错）；开骨架 round join 的 line/cubic 翻转仍经统一成 cubic 后保持 `Drawing.signature()` 跨字重稳定）；单轮廓一律 `ink`（必要时翻成 CCW）；环：最大 |area| → `ink`，其余 → `counter`。
- 无角点/端点槽的 skeleton 字形：`Project` 可不配置 `corners`/`ends`，从而跳过 `apply_slots`（笔迹接合不是 Writer G1 链）。
- `blend_corners` / heal / seal **不是**本插件路径。

### 6.6 几何构造器（`draw.construct`）

全部只接收几何量，不接收 `System`，不出现字母名：

```python
def tensioned_arc(p0, t0, p1, t1, *, tension: float = 0.55) -> Fragment
    # 从 p0 沿 t0 出发、沿 t1 到达 p1 的单段三次；tension 为手柄长 / 弦长比例
def superellipse_quarter(center, rx, ry, quadrant: int, *, exponent: float) -> Fragment
    # 复用 geo.curves.superellipse_kappa
def spring(stem_edge_x: float, y_from: float, y_to: float, toward: Point,
           *, depth: float, tension: float) -> Fragment
    # 直线笔画边进入曲线的过渡段（肩 / 碗接干处），保证 G1
def diagonal_band(p_top: Point, p_bottom: Point, *, weight: float, compensate: bool = True) -> tuple[Fragment, Fragment]
    # 斜笔两条边，weight 为期望的视觉粗细，compensate 时按角度修正垂直宽
def hook(
    stem_edge_x: float,
    y_join: float,
    tip: Point,
    *,
    depth: float,
    tension: float = 0.55,
    tip_tangent: Point | None = None,
) -> Fragment
    # 竖直干边 (stem_edge_x, y_join) 出发的钩形终端：G1 离开干（竖直切线朝 tip.y），
    # 经 depth 控制的腹点到 tip；默认 tip 切线水平回指干（回卷）。两段 tensioned_arc，腹点 G1。
```

### 6.7 `System`

```python
@dataclass(frozen=True, slots=True)
class Zones:   base: float = 0; x: float; cap: float; asc: float; desc: float
@dataclass(frozen=True, slots=True)
class Overshoot:  round: float; pointed: float

@dataclass(frozen=True, slots=True)
class System:
    upm: float
    zones: Zones
    overshoot: Overshoot
    stem: Mapping[str, float]           # 自由键，如 "lc" / "lc_h" / "uc"
    tokens: Mapping[str, float] = {}    # 项目自定义（含 space_stem_mul 等）
    slant: float = 0.0                  # Δx/Δy 斜体倾角比；0=正体；供 audit/spacing/kern
    def tuned(self, **kw) -> System
    def slant_dx(self, y, *, y0=0.0) -> float
    def map_xy(self, x, y, *, y0=0.0) -> tuple[float, float]
    def stem_direction_deg(self) -> float   # 斜体“竖笔”走向（正体=90°）
```

不得有 `aperture` / `roundness` 这类“一个数影响多处几何”的旋钮。
``slant`` 是几何事实（整副字的倾角），不是多处扇出的风格旋钮；斜体项目应设 ``System.slant``，不要只把倾角藏进 ``tokens["slant"]``。

Typed intent（``Intent`` / ``Brief``，``typekernel.system.intent``）把散文 brief 接到数值表：封闭词表映射到 ``slant`` / ``stem`` / ``pen_*`` / 宽比 token；``tk audit`` 在越界时告警。**不是**美学打分，也不生成字形。


### 6.8 `Project` / `@glyph` / `Master`

```python
@dataclass(frozen=True, slots=True)
class Master:
    name: str
    system: System

def glyph(name: str, *, group: str = "") -> Callable[[GlyphFn], GlyphFn]:
    """Register a glyph builder. ``fn(system) -> Drawing``.

    Attach master overrides with ``@fn.master("Black")`` on a second function
    of the same shape. Glyph ``name`` is a production name (may be a letter in
    *projects*); kernel tests must still use synthetic names（见第 7 节第 5 条）。
    """

@dataclass(frozen=True, slots=True)
class GlyphSpec:
    name: str
    group: str
    build: Callable[[System], Drawing]
    masters: Mapping[str, Callable[[System], Drawing]]  # override builders

class Project:
    def __init__(
        self,
        system: System,
        glyphs: str | Path,
        *,
        masters: Sequence[Master] = (),
        corners: Mapping[str, CornerFiller] | None = None,
        ends: Mapping[str, EndFiller] | None = None,
        default_advance: float | None = None,
    ) -> None: ...
    def discover(self) -> None:
        """Import every ``*.py`` under ``glyphs`` and collect ``@glyph`` specs."""
    def specs(self) -> Mapping[str, GlyphSpec]: ...
    def evaluate(self, name: str, *, master: str | None = None) -> Drawing:
        """Run the glyph (or its master override) with the resolved System.
        Applies ``corners`` / ``ends`` via ``apply_slots`` when configured.
        """
    def to_glyph(self, name: str, *, master: str | None = None, advance: float | None = None) -> "font.Glyph":
        """``evaluate`` then wrap contours as ``font.Glyph`` (advance default:
        bbox width, or ``default_advance``, or ``tokens['advance']``)."""
```

规则：

- `@glyph` 注册发生在模块 import 时；`discover()` 负责把 `glyphs/` 加进导入路径并加载。
- 默认母版用 `Project.system`；`masters` 里同名覆盖 `System`，字形侧 `@build.master(name)` 覆盖画法。
- `Project` / `glyph` / `Master` / `GlyphSpec` 是内核公开符号。

---

## 7. 架构守卫

`tests/architecture/test_boundaries.py`，对内核包生效：

1. 禁止 import `typekernel.parts`（对全仓生效）。
2. 函数名不得匹配 `^(build_[A-Za-z]|[A-Za-z]_|[a-z]+_from_[A-Za-z]|\w+_yoke)$`。
3. 源码不得出现 `style.serif`、`italic_slant_deg`、`vf_compat`。
4. `plugins/<x>/` 不得 import `plugins/<y>/`；任何新包不得 import 其他模块的 `_` 私有名。
5. 内核测试（`tests/draw`、`tests/system`、`tests/project`）里不得出现字母字形名字符串（用一个小正则：单字母 glyph 名或 `uniXXXX`）；需要形状时用合成夹具。
6. **构件不组字**：`anatomy` 公开函数只返回 `Drawing` 或构件 dataclass；函数名不得含字形名，也不得以 `glyph_` / `build_` 开头。
7. **字形名字面量**：`geo` / `draw` / `system` / `project` / `font` / `compile` / `cli` / `plugins`（及目标架构中的后续包）的字符串字面量不得是单字母或 AGL 字形名（f-string 片段与 TypeVar 名除外）。光学 stem 种类由项目 `AUDIT_STEMS` 声明，内核不再按字母名猜测。

用 `ast` 扫描实现，不额外引入依赖。

---

## 8. 测试清单

全部使用合成形状。

| 测试 | 断言 |
| --- | --- |
| Fragment 首尾不接 | `ValueError` |
| Fragment 内曲线接合不 G1 且无 cusp | `ContinuityError` |
| `reversed` / `mirrored_x` | 段几何正确、节点 index 正确重映射、tag 保留 |
| Writer 画矩形 | 4 直线、无需声明角点、逆时针 |
| Writer 画“直线进曲线”且不 G1 | `ContinuityError`，信息含坐标 |
| 同上但标 `corner()` | 通过，生成一个 corner 槽 |
| `fragment()` 起点不等于当前点 | `ValueError` |
| `role="counter"` | 顺时针；节点 index 随反转重映射 |
| tag 重复 | `ValueError` |
| `signature()` | 参数不同（宽度 / stem）但同一书写程序 → 签名相等；多一段 → 不等 |
| `Drawing + Drawing` | 轮廓叠加、tag 冲突报错 |
| `apply_slots` 用测试内的假填充 | 角点被替换、仍连续、未匹配槽不变、`trim` 越界报错 |
| `tensioned_arc` / `superellipse_quarter` / `spring` | 端点、端切线正确；与相邻直线 G1 |
| `hook` | 干接合 G1；终点 = tip；腹点在干同侧且 |Δx|≈depth；默认 tip 切线回指干 |
| `diagonal_band(compensate=True)` | 垂直于笔画方向的实测宽度 = `weight`（容差 0.5 单位） |
| 单轮廓合成样例 | 一个“直干 + 拱 + 直干”的合成单轮廓（测试里叫 `arch_body`，不叫 `n`），≤ 40 行，全部节点 G1 或已声明角点 |

---

## 9. 设计禁令与边界

每条 PR 都对照这几条；任何一条被违反，说明在往回走：

1. **内核与插件里不出现字母名。** 没有 `build_H` / `*_from_n` / `n_yoke` 这类函数，也没有对某个风格值的 `if` 分支。字母几何只存在于项目（starter）里。
2. **不允许事后修缝。** 连接难看就改画这个连接的片段或元素，不加 seal / soften / relieve / blend 这类补丁。
3. **一个字形的几何不由另一个字形的函数隐式推出。** 复用靠显式 import 元素，不靠 `x_from_y(...)` 里藏几百行。
4. **新加的参数要对任何合规项目都有意义**，不能只对库自带的那副字有意义。
5. **内核测试不出现具体字母，也不锁定某副字的轮廓哈希或段数。** 需要形状时用合成夹具。
6. **agent 要改一个细节，改的是自己项目里的文件**，不需要改库。

### 有意不做

- 不做 GUI 编辑器；agent 的“编辑器”就是字形文件 + 样张。
- 不在内核里放“能自动生成全套字”的工厂（包括“方便起见”的 `build_all`）。
- 不用数值门禁冒充美学判断；美学由视觉审阅决定。
- 不做 `style_consistency` / `originality` 一类美学 AI 分；`Intent` 只做 brief→System 的显式映射与越界告警。
- 不为兼容旧 API 长期维持双轨：旧路径直接删除，git 历史即存档。


## P2 落地摘要（眼睛与判断）

已实现（细节以源码与 `tk --help` 为准；目标契约见 `docs/design/target-architecture.md`，落地后迁入本节）：

| 能力 | 入口 |
| --- | --- |
| live 渲染 / 编辑视图 | `typekernel.perceive` · `tk see` |
| 测量报告 | `tk explain --json` |
| 诊断 v2（拓扑 / 区线 / 间距 / 灰度 / 插值） | `tk audit --json/--masters/--strict` |
| 评审与任务板 | `tk review` · `tk status` |
| shipped 样张 | `tk proof`（`perceive.specimen`；`qa.proof` 为兼容 shim） |

冻结令（P0-5）在 P2 出口后解除：可新增 starter / 风格插件。

## P3 落地摘要（手艺）

| 能力 | 入口 |
| --- | --- |
| 标签语法 | `typekernel.anatomy.tags` · `tags.grammar` info |
| 解剖构件 | `typekernel.anatomy`（P3-2… 推进中） |
