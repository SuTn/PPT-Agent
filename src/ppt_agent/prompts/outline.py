from datetime import datetime


def _time_hint() -> str:
    now = datetime.now()
    quarter = (now.month - 1) // 3 + 1
    return f"当前时间：{now:%Y-%m-%d}（{now.year}年Q{quarter}）。如果涉及「最新」「今年」「当前」等时间表述，以此为基准。"


OUTLINE_PROMPT = """请根据以下需求生成一个高质量的 PPT 大纲。

## 用户需求
{requirements}
{audience_section}
{objective_section}
{time_section}
{research_section}
{materials_section}

## 第一步：判断主题类型 + 规划叙事

在输出 JSON 之前，先在脑中完成以下规划（不要输出思考过程）：

### 1.1 判断主题类型

根据需求内容判断主题类型：
- **商业分析型**（行业报告、市场分析、竞品对比）
- **技术方案型**（技术选型、架构设计、实施路径）
- **说服提案型**（融资路演、项目提案、变革推动）
- **知识教育型**（培训课程、知识分享、学术汇报）

### 1.2 选择参考结构

根据主题类型选择合适的默认结构（可灵活调整）：
- 商业分析型：cover → toc → 行业现状 → 核心发现 → 挑战分析 → 趋势展望 → ending
- 技术方案型：cover → toc → 需求背景 → 方案概览 → 方案对比 → 实施路径 → ending
- 说服提案型：cover → toc → 现状痛点 → 影响分析 → 解决方案 → 行动计划 → ending
- 知识教育型：cover → toc → 核心概念 → 发展历程 → 典型应用 → 前沿趋势 → ending

### 1.3 规划叙事主线

1. **确定核心主张**：观众看完所有幻灯片后，应该被说服/记住的**一个**核心结论是什么？
2. **选择叙事框架**：
   - **scqa**：现状→冲突→核心问题→解决方案（适合说服、提案）
   - **problem_solution**：问题→方案→效果（适合汇报、提案）
   - **chronological**：背景→进展→展望（适合回顾、规划）
   - **custom**：根据主题特点自由组织
3. **规划论点递进**：每页只推进一个论点，页与页之间要有因果或递进关系
4. **分配证据**：将研究笔记/参考材料中的数据和案例分配到最相关的论点

## 第二步：内容质量标准

### 好的大纲（追求）
- 有明确的叙事弧线，观众从封面到结尾被逐步引导
- 每页 headline 是完整陈述句，观众一眼就知道"这页的结论是什么"
- 论据为结论服务，不是信息的堆砌
- section 页标记叙事转折，toc 页预告主线

### 差的大纲（避免）
- headline 只写话题标签（如"市场分析"），观众需要自己猜含义
- 页面之间没有逻辑递进，像百科词条目录
- 每页结构完全相同，套模板感明显
- 为了凑数量而注水，论据空洞

### Action Title 规范
- headline 必须是**完整陈述句**，直接传达本页核心结论
- ✅ "企业引入自动化后交付周期缩短了 60%"
- ❌ "企业自动化实践"（只是话题标签，不是结论）
- **长度硬限制**：cover 和 ending 页 headline ≤ 20 字，content 和 section 页 ≤ 25 字。超出时精简措辞而非删减结论

### section 页使用规则
- 用 `layout: "section"` 标记叙事阶段的**转折点**（如从 situation 进入 complication）
- section 页不包含 supporting_points，只用 headline 概括接下来的叙事阶段
- 典型用法：在 cover → toc 之后，用 section 页分隔各叙事阶段
- 不要过度使用：5-8 页的简单演示可能只需要 0-1 个 section 页

### TOC 页内容规则
- TOC 页的 supporting_points 必须逐条列出后续各 section 页的 headline
- 章节条目必须与大纲中实际的 section 页一一匹配，不得自创通用话题标签
- 格式：`supporting_points: [{{"message": "section 页的完整 headline", "evidence": []}}, ...]`

### body_text 使用规则
- 用 `body_text` 提供 1-2 句补充说明，帮助理解 headline 的背景或语境
- 不要把 supporting_points 的内容放到 body_text 中
- cover/toc/section/ending 页不需要 body_text

### 论据使用原则
- 每页聚焦一个核心论点，supporting_points 数量根据内容需要决定
- evidence_type：data（数据）、case_study（案例）、quote（引用）、analysis（分析）、analogy（类比）
- 有力的证据一个就够了，不要凑数
- 当 evidence 包含多个独立实体的对比数据时（如多品牌/多方案/多指标），应拆分为多个 supporting_point，每个 point 聚焦一个实体或维度，方便后续映射为表格行或图表数据点
- 如果上方有研究笔记，优先使用标注为 [已验证] 或 [行业共识] 的事实
- 避免使用标注为 [待验证] 的信息作为核心论据
- 不要编造具体数据。如果研究笔记中没有确切数字，用定性描述代替
- 如果研究笔记将某主题标注为「研究空白」或「知识空白」，不应为其创建独立 content 页；可在结尾 ending 页简要点及，或合并到相关 content 页作为补充

### 视觉元素（visual_hint）
当内容适合用特定视觉形式呈现时，在 `visual_hint` 字段标注：
- `table`：多维度数据对比（3+ 个对比项）
- `comparison`：左右/上下对比（如方案 A vs B、变革前后）
- `timeline`：时间线（发展历程、里程碑，3+ 个时间节点）
- `process`：流程/步骤（实施路径、工作流，3-5 个步骤）
- `chart`：数据趋势、占比分布
- `quote_highlight`：金句/核心观点突出展示
- 留空：默认列表布局

只在内容确实需要时使用，不必每页都指定。

## 第三步：自查（不要输出，在脑中完成）

1. **headline 检查**：每个 content/section 页的 headline 是否为**完整陈述句**（不是"市场分析"这种话题标签）？如果有话题标签式的 headline，改为结论句。
2. **递进检查**：从第一页到最后一页，读者能否被逐步引导到核心结论？如果某页与前页没有递进关系，调整或合并。
3. **论据检查**：有没有 content 页的 supporting_points 是空洞的泛泛而谈？如果有，补充具体证据或删除。
4. **visual_hint 检查**：是否有内容天然适合表格、对比、时间线等视觉形式但 visual_hint 留空了？反过来，是否有没有数据支撑却标了 chart 的页面？
5. **section 页检查**：section 页的 headline 是否清楚标记了叙事转折？是否过多或过少？

确认无误后再输出 JSON。

## 第四步：输出 JSON

严格按以下结构输出，不要输出 JSON 以外的任何内容。

```json
{{
  "title": "演示文稿标题",
  "audience": "目标受众（如：企业高管、技术团队、客户等）",
  "objective": "persuade / report / educate / inspire",
  "narrative": {{
    "framework": "scqa / problem_solution / chronological / custom",
    "situation": "现状/背景",
    "complication": "冲突/挑战",
    "core_question": "核心问题",
    "core_answer": "核心回答/主张"
  }},
  "slides": [
    {{
      "page": 1,
      "layout": "cover",
      "headline": "完整陈述句形式的主标题",
      "supporting_points": []
    }},
    {{
      "page": 2,
      "layout": "toc",
      "headline": "概括演示主线的标题",
      "supporting_points": [
        {{"message": "第一个 section 页的 headline", "evidence": []}},
        {{"message": "第二个 section 页的 headline", "evidence": []}}
      ]
    }},
    {{
      "page": 3,
      "layout": "section",
      "headline": "叙事阶段转折的结论句",
      "section": "situation",
      "supporting_points": []
    }},
    {{
      "page": 4,
      "layout": "content",
      "headline": "本页核心结论（完整陈述句）",
      "body_text": "补充说明（1-2句，可选）",
      "supporting_points": [
        {{
          "message": "支撑结论的论点",
          "evidence": [
            {{"claim": "具体数据或案例", "evidence_type": "data"}}
          ]
        }}
      ],
      "speaker_notes": "演讲者备注",
      "section": "situation / complication / answer / ...",
      "visual_hint": "table / comparison / timeline / process / chart / quote_highlight 或留空"
    }}
  ]
}}
```

## 示例（节选）

主题：「远程办公如何重塑企业管理」

```json
{{
  "title": "远程办公已将管理重心从工时监控转向成果交付",
  "audience": "企业中层管理者",
  "objective": "persuade",
  "narrative": {{
    "framework": "scqa",
    "situation": "远程办公从应急措施变为长期常态",
    "complication": "传统基于工时的管理模式在远程环境下失效",
    "core_question": "如何在远程环境下保持团队高效运作？",
    "core_answer": "转向成果导向的管理模式，建立信任文化和异步协作机制"
  }},
  "slides": [
    {{"page": 1, "layout": "cover", "headline": "远程时代，管理从「看得见」转向「信得过」", "supporting_points": []}},
    {{"page": 2, "layout": "toc", "headline": "从现状到方案：远程管理模式的四个关键转变", "supporting_points": [{{"message": "远程办公已成为不可逆转的工作方式", "evidence": []}}, {{"message": "传统管理模式在远程环境下全面失效", "evidence": []}}]}},
    {{"page": 3, "layout": "section", "headline": "远程办公已成为不可逆转的工作方式", "section": "situation", "supporting_points": []}},
    {{
      "page": 4, "layout": "content", "headline": "全球 74% 的企业已采用混合办公模式",
      "supporting_points": [{{"message": "混合办公渗透率持续攀升", "evidence": [{{"claim": "麦肯锡 2024 报告：74% 受访企业采用混合模式", "evidence_type": "data"}}]}}],
      "section": "situation", "visual_hint": "chart"
    }},
    {{"page": 5, "layout": "section", "headline": "传统管理模式在远程环境下全面失效", "section": "complication", "supporting_points": []}},
    {{
      "page": 6, "layout": "content", "headline": "工时监控型管理导致远程员工敬业度下降 35%",
      "body_text": "「看得见才算在工作」的思维与远程环境根本冲突",
      "supporting_points": [{{"message": "微观管理适得其反", "evidence": [{{"claim": "Gallup 调查：被密切监控的远程员工敬业度显著更低", "evidence_type": "data"}}]}}],
      "section": "complication", "visual_hint": "comparison"
    }}
  ]
}}
```

注意示例中的关键模式：
- cover 的 headline 就是核心主张的浓缩
- section 页不定期出现，仅在叙事转折处使用
- content 页的 headline 是具体结论句，不是话题标签
- evidence 提供具体来源，不是空洞描述

- cover 和 ending 页不需要 supporting_points
- toc 页的 supporting_points 列出各 section 页的 headline，一一对应
- toc 页 headline 概括演示主线
- section 页 headline 是该章节的核心结论
- 从用户需求中推断 audience 和 objective，据此调整术语深度
- 如果上方有研究笔记，将关键发现融入 supporting_points 和 evidence
- 如果上方有参考材料，将数据融入 evidence
{page_instruction}

只输出 JSON，不要其他内容。"""


def _materials_section(materials: str = "") -> str:
    if not materials or not materials.strip():
        return ""
    preview = materials[:6000] if len(materials) > 6000 else materials
    return f"## 参考材料\n\n以下是用户上传的参考文档内容，请从中提取关键信息融入大纲：\n\n{preview}\n\n"


def _research_section(research: str = "") -> str:
    if not research or not research.strip():
        return ""
    preview = research[:8000] if len(research) > 8000 else research
    return f"## 研究笔记\n\n以下是针对该主题的深度研究结果，请据此构建有深度的大纲：\n\n{preview}\n\n"


def _audience_section(audience: str = "") -> str:
    if not audience or not audience.strip():
        return ""
    return f"\n**目标受众**：{audience}\n"


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
    return f"**演示目标**：{label}\n"
