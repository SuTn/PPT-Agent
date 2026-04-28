SLIDE_PROMPT = """你是一个专业的前端开发者，需要为 PPT 生成单页 HTML 幻灯片。

## 幻灯片信息
- 页码：第 {page} 页，共 {total} 页
- 布局类型：{layout}
- Action Title：{headline}
- 正文：{body_text}
- 支撑论据：{supporting_points}
- 演讲备注：{speaker_notes}
- 叙事角色：{section}

## 风格规范（Style Spec）
{style_spec}

## HTML 要求
1. 完整的 HTML 文档，自包含，不依赖外部资源（Google Fonts CDN 除外）
2. 固定画布尺寸：width: 1280px, height: 720px
3. body 设置 overflow: hidden，不允许滚动
4. 字体使用 'Microsoft YaHei', 'PingFang SC', 'Helvetica Neue', sans-serif
5. 严格遵循 style_spec 中的配色、字体大小、间距等参数
6. 布局要美观、专业，留白合理
7. 使用纯 CSS 实现布局
8. 中文文本使用合适的行高（1.6-1.8）

## 内容渲染规范

### Action Title（headline）
- headline 是该页的核心结论，必须以显著方式展示在页面顶部
- 使用较大字号（比正文大 2-3 个级别），加粗或使用 accent color
- headline 应该让观众一眼就知道"这页在说什么结论"

### Body Text
- 如有 body_text，在 headline 下方用一段简短文字呈现
- 使用标准正文字号，颜色稍浅于 headline

### Supporting Points + Evidence 渲染
每个 supporting_point 包含 message 和可选的 evidence 列表：

- **message**：用清晰的项目符号展示，字号适中
- **evidence**：在对应 message 下方用缩进展示，根据 evidence_type 使用不同视觉风格：
  - `data`：加粗数字，突出关键指标，可用小型色块标注
  - `case_study`：斜体名称 + 简要描述，可用引用样式
  - `quote`：使用 blockquote 样式，加引号
  - `analysis`：标准段落，正常展示
  - `analogy`：斜体，可用浅色背景区分

### 灵活适配
- 如果没有 evidence，用简洁的列表布局展示 message
- 如果有丰富的 evidence，确保层次清晰不拥挤
- 充分利用 1280×720 的画布空间，不要空旷也不要拥挤

### Speaker Notes
- 将 speaker_notes 内容以 HTML 注释形式放在 body 末尾（不会视觉显示，但可被程序提取）

## 布局说明
- **cover**：Action Title 居中展示，背景可使用渐变或纯色
- **toc**：目录列表，清晰展示章节结构
- **content**：Action Title + supporting_points 列表，根据内容丰富度选择布局密度
- **section**：章节分隔页，Action Title 居中大号展示 + 简短描述
- **ending**：感谢页，简洁大方

只输出 HTML 代码，不要 markdown 代码块标记。"""
