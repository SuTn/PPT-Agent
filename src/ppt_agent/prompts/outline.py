OUTLINE_PROMPT = """请根据以下需求生成一个高质量的 PPT 大纲。

## 用户需求
{requirements}

{research_section}
{materials_section}
## 第一步：规划叙事主线

在输出 JSON 之前，先在脑中完成以下规划（不要输出思考过程）：

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
- 保持简短有力，避免超过 20 字

### 论据使用原则
- 每页聚焦一个核心论点，supporting_points 数量根据内容需要决定
- evidence_type：data（数据）、case_study（案例）、quote（引用）、analysis（分析）、analogy（类比）
- 有力的证据一个就够了，不要凑数

### 视觉元素（visual_hint）
当内容适合用特定视觉形式呈现时，在 `visual_hint` 字段标注：
- `table`：数据对比表格（如：多维度指标对比）
- `comparison`：左右或上下对比（如：方案 A vs 方案 B、变革前后）
- `timeline`：时间线（如：发展历程、里程碑）
- `process`：流程/步骤（如：实施路径、工作流）
- `chart`：图表（如：趋势变化、占比分布）
- `quote_highlight`：金句/引用突出展示（如：核心观点、名言）
- 留空：默认列表布局

只在内容确实需要时使用，不必每页都指定。

## 第三步：自查（不要输出，在脑中完成）

1. 逐页检查 headline：每个 content/section 页的 headline 是否为**完整陈述句**（不是"市场分析"这种话题标签）？如果有话题标签式的 headline，改为结论句。
2. 页面间逻辑递进：从第一页到最后一页，读者能否被逐步引导到核心结论？如果某页与前页没有递进关系，调整或合并。
3. visual_hint 使用：是否有内容天然适合表格、对比、时间线等视觉形式但 visual_hint 留空了？

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
      "supporting_points": []
    }},
    {{
      "page": 3,
      "layout": "content",
      "headline": "本页核心结论（完整陈述句）",
      "body_text": "补充说明（1-2句）",
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

- cover 和 ending 页不需要 supporting_points
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
