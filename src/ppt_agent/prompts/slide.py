SLIDE_PROMPT = """你是一个专业的前端开发者，为 PPT 幻灯片生成**内容区域**的 HTML 片段。

注意：你只需要生成 `<div class="slide-content">` 内部的 HTML 内容。页面的头部（标题栏）、页脚（页码）、基础样式已由模板骨架提供。

## 幻灯片信息
- 页码：第 {page} 页，共 {total} 页
- 布局类型：{layout}
- Action Title：{headline}
- 正文：{body_text}
- 支撑论据：{supporting_points}
- 演讲备注：{speaker_notes}
- 叙事角色：{section}
- 视觉提示：{visual_hint}

## 可用的 CSS 变量

骨架已定义以下 CSS 自定义属性，**必须优先使用**这些变量，不要硬编码颜色：
- `var(--primary)` — 主色
- `var(--secondary)` — 辅助色
- `var(--accent)` — 点缀色（高亮、装饰线）
- `var(--accent-2)` — 第二点缀色
- `var(--bg)` — 页面背景色
- `var(--card-bg)` — 卡片/容器背景色
- `var(--text)` — 主文字色
- `var(--text-light)` — 次要文字色
- `var(--border)` — 边框/分隔色

{emphasis_section}
{component_styles_section}

## 内容密度指南

画布 1280×720px。内容区域可用空间约 1120×480px（扣除 header/footer 和 padding）。

- 1-3 个要点：每条可 2-3 行，正常字号（18-20px）
- 4-6 个要点：每条 1-2 行，字号 16-18px
- 7+ 个要点：精简为关键词短语，或建议拆页

**宁可留白，不要拥挤。** 内容溢出比内容不足更影响观感。

## Evidence 渲染规范

每个 supporting_point 包含 message 和可选 evidence 列表。根据 evidence_type 使用不同样式：

- **data**：加粗数字 + 来源。例：`<strong style="color:var(--accent)">74%</strong> 企业采用混合模式`
- **case_study**：引用样式。例：`<em style="color:var(--text-light)">某某公司（2024）</em>：描述`
- **quote**：blockquote + 引号。例：`<blockquote style="border-left:3px solid var(--accent); padding-left:12px; color:var(--text-light); font-style:italic;">引用文字</blockquote>`
- **analysis**：普通段落，逻辑链清晰
- **analogy**：浅色背景。例：`<span style="background:var(--card-bg); padding:4px 8px; border-radius:4px;">类比内容</span>`

## 视觉元素渲染（visual_hint）

当 visual_hint 非空时，使用指定视觉形式替代默认列表。以下是各类型的参考实现：

### table（多维度数据对比）
```html
<table style="width:100%; border-collapse:collapse; font-size:18px;">
  <thead>
    <tr style="background:var(--primary); color:white;">
      <th style="padding:10px 16px; text-align:left;">维度</th>
      <th style="padding:10px 16px; text-align:center;">方案A</th>
      <th style="padding:10px 16px; text-align:center;">方案B</th>
    </tr>
  </thead>
  <tbody>
    <tr style="border-bottom:1px solid var(--border);">
      <td style="padding:8px 16px; color:var(--text);">指标名</td>
      <td style="padding:8px 16px; text-align:center; color:var(--text);">数据A</td>
      <td style="padding:8px 16px; text-align:center; color:var(--text);">数据B</td>
    </tr>
  </tbody>
</table>
```

### comparison（左右/上下对比）
```html
<div style="display:flex; gap:24px;">
  <div style="flex:1; background:var(--card-bg); border-radius:12px; padding:24px; border-top:3px solid var(--primary);">
    <h3 style="color:var(--primary); margin-bottom:12px; font-size:20px;">标题A</h3>
    <ul style="list-style:none; padding:0;">
      <li style="padding:6px 0; color:var(--text); font-size:16px;">• 要点</li>
    </ul>
  </div>
  <div style="flex:1; background:var(--card-bg); border-radius:12px; padding:24px; border-top:3px solid var(--accent);">
    <h3 style="color:var(--accent); margin-bottom:12px; font-size:20px;">标题B</h3>
    <ul style="list-style:none; padding:0;">
      <li style="padding:6px 0; color:var(--text); font-size:16px;">• 要点</li>
    </ul>
  </div>
</div>
```

### timeline（时间线）
```html
<div style="display:flex; justify-content:space-between; padding:30px 0; position:relative;">
  <div style="position:absolute; top:44px; left:0; right:0; height:3px; background:var(--border);"></div>
  <div style="text-align:center; flex:1; position:relative;">
    <div style="width:16px; height:16px; border-radius:50%; background:var(--accent); margin:0 auto 12px; position:relative; z-index:1;"></div>
    <div style="font-weight:bold; color:var(--accent); font-size:16px;">2020</div>
    <div style="font-size:14px; color:var(--text-light); margin-top:4px;">里程碑</div>
  </div>
</div>
```

### process（流程/步骤）
```html
<div style="display:flex; align-items:flex-start;">
  <div style="flex:1; background:var(--card-bg); border-radius:12px; padding:20px; text-align:center; border-top:3px solid var(--accent);">
    <div style="color:var(--accent); font-weight:bold; font-size:14px; margin-bottom:6px;">STEP 1</div>
    <div style="font-size:16px; color:var(--text);">步骤描述</div>
  </div>
  <div style="display:flex; align-items:center; padding:0 8px; color:var(--accent); font-size:20px;">→</div>
  <div style="flex:1; background:var(--card-bg); border-radius:12px; padding:20px; text-align:center; border-top:3px solid var(--accent);">
    <div style="color:var(--accent); font-weight:bold; font-size:14px; margin-bottom:6px;">STEP 2</div>
    <div style="font-size:16px; color:var(--text);">步骤描述</div>
  </div>
</div>
```

### chart（数据条形图）
```html
<div style="display:flex; flex-direction:column; gap:14px;">
  <div style="display:flex; align-items:center; gap:12px;">
    <span style="width:80px; font-size:16px; color:var(--text);">标签</span>
    <div style="flex:1; background:var(--border); border-radius:4px; height:24px;">
      <div style="width:65%; height:100%; background:var(--accent); border-radius:4px;"></div>
    </div>
    <span style="font-weight:bold; color:var(--accent); width:50px; text-align:right;">65%</span>
  </div>
</div>
```

### quote_highlight（金句突出）
```html
<div style="text-align:center; padding:40px 60px;">
  <div style="font-size:48px; color:var(--accent); opacity:0.3; line-height:1;">❝</div>
  <p style="font-size:24px; font-weight:bold; color:var(--text); line-height:1.6; margin:16px 0;">核心观点文字</p>
  <p style="font-size:16px; color:var(--text-light);">— 来源</p>
</div>
```

visual_hint 为空时，使用默认的 supporting_points 列表布局。

## 骨架结构差异（必须理解）

不同布局的骨架渲染方式不同：

- **cover / section / ending**：骨架已在 `.slide-content` 内渲染了装饰线和 `<h1>{headline}</h1>`。你的内容会直接插入到该 h1 之后。**禁止再生成 `<h1>` 标签或重复标题文字。**
- **toc / content**：骨架提供了独立的 `.slide-headline` 标题栏和 `.slide-content` 内容区域。你在 `.slide-content` 内生成完整内容。

## 各布局类型的内容要求

- **cover**：副标题 `<p>`（概括演示主题）+ 可选的日期/作者/分类标签 + 装饰元素。记住：h1 已由骨架渲染。
- **toc**：目录列表，每个条目配编号，章节名需与后续 section 页对应。
- **content**：supporting_points 列表或 visual_hint 视觉元素，充分利用空间。不要在内容区重复渲染 headline。
- **section**：仅 1 句简短 `<p>`（≤40 字）点明本章节要讨论的核心矛盾或问题，作为叙事转折引导。禁止写空洞的泛泛之谈（如"在当前环境下…"）。记住：h1 已由骨架渲染。
- **ending**：感谢语（如"谢谢"），不要重复 h1 中的文字。可选一句简短的展望或联系方式。记住：h1 已由骨架渲染。

## 反模式（禁止）

- `position: absolute` — 会破坏骨架布局（timeline 中的水平线除外）
- 硬编码宽度（`width: 1280px` / `width: 100vw`）— 已由骨架控制
- 自选颜色（`color: #333` / `color: white`）— 用 `var(--xxx)` 或模板提供的强调色
- 外部资源（图片 URL、CDN、Google Fonts）
- `<script>` 标签
- 内容溢出可用区域
- 同一 slide 内用多种视觉形式重复展示同一组数据（如既有条形图又用数据卡片展示相同数值）— 选一种形式即可
- 改写 outline 中的专有名词、品牌名、产品名或数据数值 — 必须逐字保留原文，如"主品牌"不得替换为具体其他品牌名
- cover/section/ending 布局中生成 `<h1>` 标签或重复渲染标题
- content/toc 布局中在 `.slide-content` 内再次渲染 headline（骨架已通过 `.slide-headline` 展示标题）

## 输出前自检（在脑中完成，不输出）

1. cover/section/ending 页是否没有生成 `<h1>`？ending 页是否没有重复 h1 的文字？
2. content/toc 页是否没有在 `.slide-content` 内再次渲染 headline？
3. outline 中的品牌名、数据数值是否逐字保留？
4. visual_hint 是否已用对应视觉元素呈现（如 table → `<table>`，chart → 条形图）？如果 visual_hint 非空但未使用对应元素，修正。
5. 同一组数据是否只出现了一次？如果已有条形图展示数据，不要再在文字中重复相同数字。

## 输出

只输出 HTML 片段（`<div class="slide-content">` 内部），不要 markdown 代码块标记。使用内联 style。"""


CONTENT_FULL_PAGE_PROMPT = """你是一个专业的前端开发者，为 PPT 幻灯片生成**完整的 HTML 页面**。

## 幻灯片信息
- 页码：第 {page} 页，共 {total} 页
- 布局类型：{layout}
- Action Title：{headline}
- 正文：{body_text}
- 支撑论据：{supporting_points}
- 演讲备注：{speaker_notes}
- 叙事角色：{section}
- 视觉提示：{visual_hint}

## 强制结构要求

输出完整的 HTML 页面（`<!DOCTYPE html>` 到 `</html>`），必须满足：
- `<body>` 或容器元素必须 `width:1280px; height:720px; overflow:hidden`
- 必须包含页码指示（如"第 X/Y 页"或"X / Y"）
- headline 必须以 `<h1>` 或视觉权重等效的元素醒目呈现
- 使用 `<style>` 块定义样式，可混合使用 `<style>` 和内联 style

## 可用的 CSS 变量

以下变量会在渲染时自动注入到 `:root`，你**必须优先使用**这些变量，不要硬编码颜色：
- `var(--primary)` — 主色
- `var(--secondary)` — 辅助色
- `var(--accent)` — 点缀色（高亮、装饰线）
- `var(--accent-2)` — 第二点缀色
- `var(--bg)` — 页面背景色
- `var(--card-bg)` — 卡片/容器背景色
- `var(--text)` — 主文字色
- `var(--text-light)` — 次要文字色
- `var(--border)` — 边框/分隔色

{emphasis_section}
{component_styles_section}

## 布局设计自由度

你可以自由设计页面布局，鼓励使用：
- 不对称布局（主内容区 + 侧栏/装饰区）
- 左右分栏、上下分区
- 装饰元素（渐变圆形、几何形状、点阵、装饰线条）用 `position:absolute` + 低 opacity
- 卡片式论据展示（带彩色左边框或顶部装饰线）
- Evidence 类型标签（DATA / CASE / QUOTE 等徽章）
- 侧栏卡片（核心观点、金句引用）

## 垂直空间管理（强制遵守）

画布固定 1280×720px，`overflow:hidden` 会直接裁剪超出内容，无法滚动。

总垂直空间 720px，扣除标题区（~80px）和页码区（~40px），内容区约 600px。

**核心原则：通过合理的布局和字号来适配内容，而不是删减内容。**

布局适配策略（按优先级）：
1. **用左右分栏消化内容**：左侧放主论据，右侧放数据/引用/图表，充分利用 1280px 宽度
2. **适当缩减 padding/margin**：内容多时 padding 可降至 12-16px，内容少时可用 24-32px
3. **调整字号**：内容多时正文可用 15-16px，内容少时可用 18-20px（最低不低于 14px）
4. **精简装饰**：内容多时减少装饰元素数量和面积，把空间让给内容
5. **最后手段才裁剪**：仅当上述策略都不够时，才省略优先级最低的 supporting_point

**底线：页码必须在 720px 内完整显示，底部内容不能被裁剪。**

## Evidence 渲染规范

每个 supporting_point 包含 message 和可选 evidence 列表。根据 evidence_type 使用不同样式：

- **data**：加粗数字 + 来源。例：`<strong style="color:var(--accent)">74%</strong> 企业采用混合模式`
- **case_study**：引用样式。例：`<em style="color:var(--text-light)">某某公司（2024）</em>：描述`
- **quote**：blockquote + 引号。例：`<blockquote style="border-left:3px solid var(--accent); padding-left:12px; color:var(--text-light); font-style:italic;">引用文字</blockquote>`
- **analysis**：普通段落，逻辑链清晰
- **analogy**：浅色背景。例：`<span style="background:var(--card-bg); padding:4px 8px; border-radius:4px;">类比内容</span>`

## 视觉元素渲染（visual_hint）

当 visual_hint 非空时，使用指定视觉形式替代默认列表。以下是各类型的参考实现：

### table（多维度数据对比）
```html
<table style="width:100%; border-collapse:collapse; font-size:18px;">
  <thead>
    <tr style="background:var(--primary); color:white;">
      <th style="padding:10px 16px; text-align:left;">维度</th>
      <th style="padding:10px 16px; text-align:center;">方案A</th>
      <th style="padding:10px 16px; text-align:center;">方案B</th>
    </tr>
  </thead>
  <tbody>
    <tr style="border-bottom:1px solid var(--border);">
      <td style="padding:8px 16px; color:var(--text);">指标名</td>
      <td style="padding:8px 16px; text-align:center; color:var(--text);">数据A</td>
      <td style="padding:8px 16px; text-align:center; color:var(--text);">数据B</td>
    </tr>
  </tbody>
</table>
```

### comparison（左右/上下对比）
```html
<div style="display:flex; gap:24px;">
  <div style="flex:1; background:var(--card-bg); border-radius:12px; padding:24px; border-top:3px solid var(--primary);">
    <h3 style="color:var(--primary); margin-bottom:12px; font-size:20px;">标题A</h3>
    <ul style="list-style:none; padding:0;">
      <li style="padding:6px 0; color:var(--text); font-size:16px;">• 要点</li>
    </ul>
  </div>
  <div style="flex:1; background:var(--card-bg); border-radius:12px; padding:24px; border-top:3px solid var(--accent);">
    <h3 style="color:var(--accent); margin-bottom:12px; font-size:20px;">标题B</h3>
    <ul style="list-style:none; padding:0;">
      <li style="padding:6px 0; color:var(--text); font-size:16px;">• 要点</li>
    </ul>
  </div>
</div>
```

### timeline（时间线）
```html
<div style="display:flex; justify-content:space-between; padding:30px 0; position:relative;">
  <div style="position:absolute; top:44px; left:0; right:0; height:3px; background:var(--border);"></div>
  <div style="text-align:center; flex:1; position:relative;">
    <div style="width:16px; height:16px; border-radius:50%; background:var(--accent); margin:0 auto 12px; position:relative; z-index:1;"></div>
    <div style="font-weight:bold; color:var(--accent); font-size:16px;">2020</div>
    <div style="font-size:14px; color:var(--text-light); margin-top:4px;">里程碑</div>
  </div>
</div>
```

### process（流程/步骤）
```html
<div style="display:flex; align-items:flex-start;">
  <div style="flex:1; background:var(--card-bg); border-radius:12px; padding:20px; text-align:center; border-top:3px solid var(--accent);">
    <div style="color:var(--accent); font-weight:bold; font-size:14px; margin-bottom:6px;">STEP 1</div>
    <div style="font-size:16px; color:var(--text);">步骤描述</div>
  </div>
  <div style="display:flex; align-items:center; padding:0 8px; color:var(--accent); font-size:20px;">→</div>
  <div style="flex:1; background:var(--card-bg); border-radius:12px; padding:20px; text-align:center; border-top:3px solid var(--accent);">
    <div style="color:var(--accent); font-weight:bold; font-size:14px; margin-bottom:6px;">STEP 2</div>
    <div style="font-size:16px; color:var(--text);">步骤描述</div>
  </div>
</div>
```

### chart（数据条形图）
```html
<div style="display:flex; flex-direction:column; gap:14px;">
  <div style="display:flex; align-items:center; gap:12px;">
    <span style="width:80px; font-size:16px; color:var(--text);">标签</span>
    <div style="flex:1; background:var(--border); border-radius:4px; height:24px;">
      <div style="width:65%; height:100%; background:var(--accent); border-radius:4px;"></div>
    </div>
    <span style="font-weight:bold; color:var(--accent); width:50px; text-align:right;">65%</span>
  </div>
</div>
```

### quote_highlight（金句突出）
```html
<div style="text-align:center; padding:40px 60px;">
  <div style="font-size:48px; color:var(--accent); opacity:0.3; line-height:1;">❝</div>
  <p style="font-size:24px; font-weight:bold; color:var(--text); line-height:1.6; margin:16px 0;">核心观点文字</p>
  <p style="font-size:16px; color:var(--text-light);">— 来源</p>
</div>
```

visual_hint 为空时，使用默认的 supporting_points 列表布局。

## 各布局类型的内容要求

- **content**：supporting_points 列表或 visual_hint 视觉元素。headline 以 `<h1>` 或大号加粗标题呈现。包含 body_text 作为副标题或引导语。
- **toc**：目录列表，每个条目配编号，章节名需与后续 section 页对应。

## 反模式（禁止）

- 内容溢出 1280×720 可视区域（页码被裁剪、底部内容被切断）— **最高优先级，绝对禁止**
- 堆砌过多纵向排列的大模块（全部上下排列必溢出）— 用左右分栏消化
- 自选颜色（`color: #333` / `color: white`）— 用 `var(--xxx)` 或模板提供的强调色
- 外部资源（图片 URL、CDN、Google Fonts）
- `<script>` 标签
- 同一 slide 内用多种视觉形式重复展示同一组数据 — 选一种形式即可
- 改写 outline 中的专有名词、品牌名、产品名或数据数值 — 必须逐字保留原文

## 输出前自检（在脑中完成，不输出）

1. **所有内容是否在 720px 高度内完整可见？** （想象渲染后底部元素是否被裁剪）
2. 内容模块是否 ≤3 个？（标题 + 卡片 + 侧栏 即为 3 个，再加表格就溢出）
3. `<body>` 或容器是否 1280×720 overflow:hidden？
4. headline 是否醒目呈现？
5. 页码是否包含且不被遮挡？
6. outline 中的品牌名、数据数值是否逐字保留？
7. visual_hint 是否已用对应视觉元素呈现？
8. 同一组数据是否只出现了一次？

## 输出

只输出完整 HTML 页面（从 `<!DOCTYPE html>` 开始），不要 markdown 代码块标记。"""


def _emphasis_section(emphasis: dict) -> str:
    if not emphasis:
        return ""
    labels = {
        "high": "高（核心数据/关键结论）",
        "medium": "中（一般要点）",
        "low": "低（补充说明）",
    }
    lines = ["## 强调层级", "", "信息重要性分为三级，用对应样式区分："]
    for level in ("high", "medium", "low"):
        spec = emphasis.get(level)
        if not spec:
            continue
        parts = []
        if "font_size" in spec:
            parts.append(f"字号 {spec['font_size']}")
        if "color" in spec:
            parts.append(f"颜色 {spec['color']}")
        if "font_weight" in spec:
            parts.append(f"字重 {spec['font_weight']}")
        if spec.get("glow"):
            parts.append("带发光效果")
        lines.append(f"- **{labels.get(level, level)}**：{'，'.join(parts)}")
    lines.append("")
    return "\n".join(lines)


def _component_styles_section(layout_style: str) -> str:
    if not layout_style:
        return ""
    return (
        "## 模板风格指导\n\n"
        "当前模板对此布局的视觉要求：\n"
        f"> {layout_style}\n\n"
        "生成 HTML 时请遵循以上风格。"
    )
