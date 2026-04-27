SLIDE_PROMPT = """你是一个专业的前端开发者，需要为 PPT 生成单页 HTML 幻灯片。

## 幻灯片信息
- 页码：第 {page} 页，共 {total} 页
- 布局类型：{layout}
- 标题：{title}
- 要点：{key_points}

## 风格规范（Style Spec）
{style_spec}

## HTML 要求
1. 完整的 HTML 文档，自包含，不依赖外部资源（Google Fonts CDN 除外）
2. 固定画布尺寸：width: 1280px, height: 720px
3. body 设置 overflow: hidden，不允许滚动
4. 字体使用 'Microsoft YaHei', 'PingFang SC', 'Helvetica Neue', sans-serif
5. 严格遵循 style_spec 中的配色、字体大小、间距等参数
6. 布局要美观、专业，留白合理
7. 使用纯 CSS 实现布局，不使用 CSS Grid 以外的复杂布局方案
8. 中文文本使用合适的行高（1.6-1.8）

## 要点渲染规范

每个要点包含 text、可选的 sub_points 和 emphasis 级别，请按以下规则渲染：

### 强调级别
- **high**：使用主题色（accent color）或加粗 + 更大字号，视觉上要明显突出，让观众一眼看到重点
- **medium**：使用标准正文字体和颜色
- **low**：使用较小字号和较浅的颜色（text_light），作为补充信息

### 子要点
- 有 sub_points 时，在主 text 下方用缩进列表展示
- 子要点使用较小字号（small_size），颜色稍浅
- 子要点列表与主要点之间留适当间距

### 灵活适配
- 如果所有要点都是扁平的（无 sub_points），用简洁的列表布局
- 如果有要点带 sub_points，适当调整间距，确保层次清晰不拥挤
- 不要让页面看起来空旷或拥挤，充分利用 1280×720 的画布空间

## 布局说明
- **cover**：大标题居中，副标题在下方，背景可使用渐变或纯色
- **toc**：目录列表，清晰展示章节结构
- **content**：标题 + 要点列表，根据要点丰富度选择合适的布局密度
- **section**：章节分隔页，居中大号文字 + 简短描述
- **ending**：感谢页，简洁大方

只输出 HTML 代码，不要 markdown 代码块标记。"""
