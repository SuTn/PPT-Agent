RESEARCH_ANALYZE_PROMPT = """你是一个专业的研究分析师，正在为演示文稿准备深度研究素材。

## 主题
{topic}
{requirements_section}
{audience_section}
{objective_section}
{materials_section}

## 任务

### 第一步：判断主题类型（在脑中完成，不输出）

根据主题内容判断类型：
- **商业分析型**（行业报告、市场分析、竞品对比）→ 侧重数据、趋势、竞争格局
- **技术方案型**（技术选型、架构设计、实施路径）→ 侧重原理、对比、实践
- **说服提案型**（融资路演、项目提案、变革推动）→ 侧重痛点、方案、ROI
- **知识教育型**（培训课程、知识分享、学术汇报）→ 侧重概念、案例、应用
- **综合型** → 混合上述维度

### 第二步：设计研究维度

根据主题类型，识别 3-5 个互斥且全面覆盖的研究维度（MECE 原则）。

维度选择参考：
- 商业分析型：市场规模、竞争格局、关键驱动因素、风险与挑战、未来趋势
- 技术方案型：核心原理、方案对比、实施难点、最佳实践、演进方向
- 说服提案型：现状痛点、解决方案、成功案例、投入产出、行动计划
- 知识教育型：核心概念、发展历程、典型应用、常见误区、前沿进展

维度数量：简单主题 3 个、中等 4 个、复杂 5 个。

### 第三步：为每个维度生成搜索查询

为每个维度生成 2 个搜索查询词（用于联网搜索）：
- 使用具体关键词，不要泛泛描述
- 包含年份或时效性关键词
- 优先使用可能搜到权威数据源的查询

## 输出格式

严格输出以下 JSON，不要包含其他内容：

```json
{{
  "topic_type": "business_analysis / technical_solution / persuasive_proposal / educational / mixed",
  "analysis_summary": "一段话概述主题核心本质和研究价值",
  "dimensions": [
    {{
      "name": "维度名称",
      "focus": "研究重点（1-2句）",
      "search_queries": ["搜索查询词1", "搜索查询词2"]
    }}
  ]
}}
```

## 示例

主题：「2025年中国新能源汽车出海战略」
```json
{{
  "topic_type": "business_analysis",
  "analysis_summary": "中国新能源汽车出海是汽车产业最重要的战略方向之一，涉及市场选择、本地化、关税政策、品牌建设等多维度挑战。",
  "dimensions": [
    {{
      "name": "目标市场格局",
      "focus": "主要出海目标市场的规模、增长率和竞争格局",
      "search_queries": ["2025年中国新能源汽车出口数据 欧洲东南亚", "比亚迪蔚来海外销量 2024 2025"]
    }},
    {{
      "name": "政策与壁垒",
      "focus": "关税政策、法规认证、地缘政治风险",
      "search_queries": ["欧盟中国电动车关税 2025最新政策", "中国车企海外建厂政策"]
    }},
    {{
      "name": "本地化挑战",
      "focus": "品牌认知、渠道建设、文化适配",
      "search_queries": ["中国新能源车欧洲品牌认知度调查", "蔚来比亚迪海外充电网络布局"]
    }},
    {{
      "name": "成功案例与路径",
      "focus": "头部企业出海策略对比和可借鉴经验",
      "search_queries": ["比亚迪欧洲市场策略案例分析", "中国车企出海最佳实践 2025"]
    }}
  ]
}}
```

只输出 JSON，不要其他内容。"""


RESEARCH_DIMENSION_PROMPT = """你是一个专业的研究分析师。请对以下演示文稿主题的特定维度进行深度研究。

## 主题
{topic}
{requirements_section}
{audience_section}
## 当前研究维度
- 维度名称：{dimension_name}
- 研究重点：{dimension_focus}
{materials_section}
{search_section}
## 研究要求

对这个维度进行深入研究，产出详细的研究笔记。

### 核心发现
- 至少 3-5 个有实质内容的核心发现
- 每个发现必须有具体支撑（数据/案例/引用），不接受空洞的泛泛而谈

### 信息可靠性分级

对每个关键陈述标注置信度：
- **[已验证]** — 来自搜索结果或参考材料的确切事实
- **[行业共识]** — 广为人知的行业常识
- **[分析推断]** — 基于已知信息的逻辑推演
- **[待验证]** — 不确定的信息，需要进一步确认

**重要**：当搜索结果提供了具体数据时，优先使用搜索结果中的事实，不要用记忆中可能过时或不准确的信息替换。

### 证据要求
- **[data]**: 给出具体数值、百分比、金额，注明来源和时间
- **[case_study]**: 给出企业/项目名称、时间、关键数据
- **[quote]**: 给出原文、说话者、场合
- **[analysis]**: 给出推理链条，而非直接下结论

避免编造数据。如果不确定具体数字，写"据行业报告"而非伪造精确数字。

### 对演示的贡献
{audience_value_hint}

## 输出格式

直接输出 Markdown 格式的研究笔记：

### 核心发现
- 发现1（附证据和置信度标注）
- 发现2
- ...

### 详细论据
- **[data] xxx** — [已验证] 来源：xxx
- **[case_study] xxx** — [行业共识] ...
- **[analysis] xxx** — [分析推断] 推理依据：xxx

### 对演示的启示
- 核心要点：这个维度最值得在幻灯片中强调的 1-2 个结论
- 受众价值：目标受众从中能获得什么

只输出 Markdown，不要包含 JSON。"""


RESEARCH_SYNTHESIZE_PROMPT = """你是一个专业的研究分析师。请将以下各维度的研究笔记综合为一份完整的演示文稿研究素材。

## 主题
{topic}
{audience_section}
{objective_section}

## 各维度研究笔记
{dimension_research}
{materials_section}
## 任务

将以上研究笔记综合整理为一份高质量的研究报告。

### 综合分析要求

1. **保留核心价值**：每个维度保留最有力的证据和最核心的发现
2. **矛盾检测**：如果不同维度的信息存在矛盾或冲突，指出并给出判断
3. **知识空白**：标注研究中发现的、但未能充分解答的重要问题
4. **叙事线索**：推荐一条能说服/打动目标受众的叙事主线

### 叙事框架

请为演示文稿建议叙事主线。优先使用 SCQA 框架：
- **Situation（现状）**：观众已知或容易接受的背景
- **Complication（冲突）**：打破现状的核心挑战或机遇
- **Question（核心问题）**：观众自然会产生的问题
- **Answer（核心回答）**：你希望观众接受的核心主张

如果不适合 SCQA，建议其他框架（problem_solution / chronological / custom），但必须给出推荐理由。

### PPT 映射建议

为研究内容建议在幻灯片中的呈现方式：
- 哪些内容适合用数据表格/图表呈现（标注 visual_hint: table/chart）
- 哪些内容适合用对比/时间线呈现（标注 visual_hint: comparison/timeline）
- 哪些数据/案例最适合在关键页面突出展示
- 建议的封面标题（Action Title 格式：完整陈述句）

## 输出格式

直接输出完整的 Markdown 格式研究报告：

# 研究笔记：{topic}

## 分析摘要
（2-3句话概括主题本质 + 为什么对目标受众重要）

## （维度一名称）
### 核心发现
- ...（保留置信度标注）
### 关键证据
- ...
### 对演示的启示
- ...

## （维度二名称）
...

## 跨维度洞察
- 各维度之间的关联和递进关系
- 矛盾与冲突点（如有）
- 研究空白（未能解答的重要问题）

## 叙事线索建议

### 推荐叙事框架：SCQA（或说明为何选择其他框架）
- **Situation**：...
- **Complication**：...
- **Question**：...
- **Answer**：...

### 维度展开顺序
1. 建议先展示...（原因）
2. 然后展开...（原因）
3. ...

### 重点展示建议
- 数据亮点：...（建议 visual_hint: chart）
- 对比要点：...（建议 visual_hint: comparison）
- 关键案例：...（建议 visual_hint: table 或 quote_highlight）
- 建议封面标题：...（Action Title 格式）

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


def _audience_section(audience: str = "") -> str:
    if not audience or not audience.strip():
        return ""
    return f"\n## 目标受众\n\n{audience}\n"


def _objective_section(objective: str = "") -> str:
    if not objective or not objective.strip():
        return ""
    obj_labels = {
        "persuade": "说服（推动行动或决策）",
        "report": "汇报（报告现状或成果）",
        "educate": "教育（传授知识或技能）",
        "inspire": "激励（激发情感或愿景）",
    }
    label = obj_labels.get(objective, objective)
    return f"\n## 演示目标\n\n{label}\n"


def _search_results_section(results: list) -> str:
    if not results:
        return ""
    parts = []
    for r in results:
        content = r.content[:500] if len(r.content) > 500 else r.content
        parts.append(f"- **{r.title}** ({r.url})\n  {content}")
    joined = "\n\n".join(parts)
    return f"\n## 网络搜索结果\n\n以下是与该研究维度相关的最新网络信息，请优先使用这些事实，引用时注明来源：\n\n{joined}\n"
