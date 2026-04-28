OUTLINE_PROMPT = """请根据以下需求生成一个 PPT 幻灯片大纲。

## 用户需求
{requirements}

{research_section}
{materials_section}
## 核心原则

### Action Title（行动标题）
- 每页的 `headline` 必须是**完整陈述句**，直接告诉观众"结论是什么"
- ✅ "全球 AI 市场规模达到 1840 亿美元，同比增长 36.8%"
- ❌ "AI 市场规模"（只是话题标签，观众需要自己解读）
- ✅ "企业采用 AI 后运营效率平均提升 40%"
- ❌ "企业 AI 应用"
- headline 控制在 15 个字以内，最多两行

### 叙事框架（Narrative）
- 选择一个叙事框架来组织整体结构：
  - **scqa**：Situation（现状）→ Complication（冲突）→ Question（问题）→ Answer（回答），适合说服性演示
  - **problem_solution**：问题 → 方案，适合提案类
  - **chronological**：按时间线展开，适合回顾/规划类
  - **custom**：其他自定义结构
- 每页通过 `section` 字段标记它在叙事中的角色（如 "situation"、"complication" 等）

### 论据层次（Supporting Points + Evidence）
- 每个 supporting_point 包含一个 `message`（核心信息）和可选的 `evidence`（支撑证据）
- evidence_type 说明证据类型：
  - `data`：具体数据/统计数字
  - `case_study`：实际案例
  - `quote`：专家观点/引用
  - `analysis`：分析推理
  - `analogy`：类比说明
- 每页 2-4 个 supporting_points，每个带 0-2 个 evidence

### 受众与目标
- 从用户需求中识别 `audience`（目标受众），据此调整术语深度
- 选择 `objective`：persuade（说服）、report（汇报）、educate（培训）、inspire（激励）
- 确定观众看完全部幻灯片后应该记住的**一个核心信息**

### 整体逻辑
- 大纲应有清晰的叙事线索，章节之间有递进关系
- section 页用于分隔主要章节，toc 页展示全局结构
- 如果下方有**研究笔记**，从中提取关键发现和证据，融入相关页面
- 如果下方有**参考材料**，从中提取数据融入 evidence

## JSON 结构

```json
{{
  "title": "演示文稿标题",
  "audience": "目标受众（如：企业高管、技术团队、客户等）",
  "objective": "persuade / report / educate / inspire",
  "narrative": {{
    "framework": "scqa / problem_solution / chronological / custom",
    "situation": "现状描述（SCQA 时使用）",
    "complication": "冲突/问题（SCQA 时使用）",
    "core_question": "核心问题",
    "core_answer": "核心回答/主张"
  }},
  "slides": [
    {{
      "page": 1,
      "layout": "cover",
      "headline": "AI 正在重塑全球产业格局",
      "supporting_points": []
    }},
    {{
      "page": 2,
      "layout": "toc",
      "headline": "今天我们将探讨三个关键问题",
      "supporting_points": []
    }},
    {{
      "page": 3,
      "layout": "content",
      "headline": "全球 AI 市场规模达到 1840 亿美元",
      "body_text": "市场增速持续加快，生成式 AI 成为最大增长引擎。",
      "supporting_points": [
        {{
          "message": "市场规模三年翻三倍，增速远超预期",
          "evidence": [
            {{"claim": "CAGR 36.8%，从 500 亿增至 1840 亿美元", "evidence_type": "data", "source": "Gartner 2024"}},
            {{"claim": "生成式 AI 占比从 12% 提升至 28%", "evidence_type": "data"}}
          ]
        }},
        {{
          "message": "企业采用率持续攀升",
          "evidence": [
            {{"claim": "企业 AI 采用率从 50% 提升至 72%", "evidence_type": "data"}},
            {{"claim": "微软 Copilot 客户案例：效率提升 40%", "evidence_type": "case_study"}}
          ]
        }}
      ],
      "speaker_notes": "重点强调增速数据，这是后续论点的基石。",
      "section": "situation"
    }},
    ...
  ]
}}
```

- 封面页（cover）和结束页（ending）不需要 supporting_points
- 目录页（toc）不需要 supporting_points，但 headline 应概括演示主线
- section 页 headline 应是该章节的核心结论
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
