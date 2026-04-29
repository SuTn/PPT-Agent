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

## 各布局类型的内容要求

- **cover**：副标题段落（`<p>`），概括演示主题。可选日期或演讲者信息
- **toc**：目录列表，每个条目配编号或圆点，章节名清晰
- **content**：supporting_points 列表或 visual_hint 视觉元素，充分利用空间
- **section**：章节描述段落（`<p>`），简短说明该章节讨论内容
- **ending**：感谢语和可选联系方式

## 反模式（禁止）

- `position: absolute` — 会破坏骨架布局（timeline 中的水平线除外）
- 硬编码宽度（`width: 1280px` / `width: 100vw`）— 已由骨架控制
- 自选颜色（`color: #333` / `color: white`）— 用 `var(--xxx)` 或模板提供的强调色
- 外部资源（图片 URL、CDN、Google Fonts）
- `<script>` 标签
- 内容溢出可用区域

## 输出

只输出 HTML 片段（`<div class="slide-content">` 内部），不要 markdown 代码块标记。使用内联 style。"""


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
