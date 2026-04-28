RESEARCH_ANALYZE_PROMPT = """你是一个专业的研究分析师。请对以下演示文稿主题进行结构化分析，识别需要深入研究的关键维度。

## 主题
{topic}
{requirements_section}
{materials_section}
## 任务

分析这个主题，识别出 3-7 个需要深入研究的关键维度（研究角度）。

要求：
- 维度之间应尽量互斥且全面覆盖（MECE 原则）
- 每个维度聚焦一个独立的研究方向
- 维度应涵盖：核心概念/定义、市场/行业数据、关键技术/方法、挑战/问题、案例/实践、趋势/前景等角度中与主题最相关的
- 每个维度附带 2-3 个引导性问题，指明研究方向

## 输出格式

```json
{{
  "analysis_summary": "一段话概述该主题的核心本质和重要性",
  "dimensions": [
    {{
      "name": "维度名称",
      "focus": "研究重点说明",
      "questions": ["引导性问题1", "引导性问题2"]
    }}
  ]
}}
```

只输出 JSON，不要其他内容。"""


RESEARCH_DIMENSION_PROMPT = """你是一个专业的研究分析师。请对以下演示文稿主题的特定维度进行深度研究。

## 主题
{topic}
{requirements_section}
## 当前研究维度
- 维度名称：{dimension_name}
- 研究重点：{dimension_focus}
- 引导性问题：{dimension_questions}
{materials_section}
## 任务

对这个维度进行深入研究，产出详细的研究笔记。

要求：
- 每个维度至少包含 2-3 个核心发现
- 尽量提供具体的数据、事实、案例
- 如果涉及数据，给出具体数值和来源
- 如果涉及案例，给出具体名称和关键细节
- 分析这个维度对整体演示的贡献——观众应该从中获得什么
- 提出这个维度与其他维度的关联

## 输出格式

直接输出 Markdown 格式的研究笔记，包含以下结构：

### 核心发现
- 发现1
- 发现2

### 论据与证据
- **[data]**: 具体数据点（附来源）
- **[case_study]**: 案例名称及关键细节
- **[quote]**: 专家观点或引用
- **[analysis]**: 分析推理
- **[analogy]**: 类比说明

### 对演示的启示
- 这个维度如何融入整体叙事

只输出 Markdown，不要包含 JSON。"""


RESEARCH_SYNTHESIZE_PROMPT = """你是一个专业的研究分析师。请将以下各维度的研究笔记综合为一份完整的研究报告。

## 主题
{topic}

## 各维度研究笔记
{dimension_research}
{materials_section}
## 任务

将以上研究笔记综合整理，要求：
- 为每个维度保留最核心的发现和最有力的证据
- 提取跨维度的关键洞察
- 建议一条叙事线索——各维度按什么顺序展开最能说服观众
- 如果适合 SCQA 框架，建议 situation/complication/question/answer 的内容
- 标注哪些数据/案例最适合在幻灯片中突出展示

## 输出格式

直接输出完整的 Markdown 格式研究报告：

# 研究笔记：{topic}

## 分析摘要
（一句话概括主题本质 + 为什么重要）

## （维度一名称）
### 核心发现
- ...
### 论据与证据
- ...
### 对演示的启示
- ...

## （维度二名称）
...

## 关键洞察
- 跨维度的核心发现1
- 跨维度的核心发现2

## 叙事线索建议
- 建议的叙事框架（如 SCQA）
- 各维度的推荐展开顺序
- 需要突出的关键数据/案例

只输出 Markdown。"""


def _research_materials_section(materials: str = "") -> str:
    if not materials or not materials.strip():
        return ""
    preview = materials[:6000] if len(materials) > 6000 else materials
    return f"\n## 参考材料\n\n以下是用户上传的参考文档，请在研究中参考：\n\n{preview}\n"


def _research_requirements_section(requirements: str = "") -> str:
    if not requirements or not requirements.strip():
        return ""
    return f"\n## 用户需求\n\n{requirements}\n"
