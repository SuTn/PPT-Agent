OUTLINE_PROMPT = """请根据以下需求生成一个 PPT 幻灯片大纲。

## 用户需求
{requirements}

{materials_section}
## 大纲质量要求

### 内容深度 — 根据内容灵活决定结构
- **简单内容**（如过渡页、概述页）：key_points 保持扁平，text 写完整陈述即可
- **复杂内容**（如核心论点、数据分析、技术细节）：需要用 sub_points 展开说明，包含数据、案例、对比等支撑信息
- **不要为了嵌套而嵌套**，只在有助于观众理解时使用 sub_points

### 要点质量
- 每个 key_point 的 text 应是**完整的陈述句或结论**，不是关键词堆砌
- 例如：✅ "2024年全球 AI 市场规模达到 1840 亿美元，同比增长 36.8%"  ❌ "AI 市场规模"
- 包含具体数据、案例或引用时，直接写进 text 或 sub_points 中

### 强调级别 — 突出重点
- `high`：该页最核心的结论、关键数据、行动号召（每页最多 1-2 个）
- `medium`：重要支撑信息（默认值，大多数要点）
- `low`：补充说明、背景信息、次要细节

### 整体逻辑
- 大纲应有清晰的**叙事线索**：问题 → 分析 → 方案 → 结论，或按时间线、模块划分
- 章节之间要有递进关系，不要堆砌并列信息
- section 页用于分隔主要章节，toc 页展示全局结构

### 受众与目标
- 从用户需求中识别**目标受众**（高管、技术人员、客户、学生等），据此调整术语深度和专业程度
- 识别**核心论点**——观众看完全部幻灯片后应该记住的那个关键信息，在大纲中用 emphasis: high 突出呈现
- 如果用户提供了具体数据、案例或材料，将其融入相关页面的 sub_points 中
- 如果下方有**参考材料**，从中提取关键数据和论点，自然融入大纲而非照搬原文

## JSON 结构

- title（演示文稿标题）
- slides 数组，每页包含：
  - page: 页码（从 1 开始）
  - layout: cover / toc / content / section / ending
  - title: 该页标题
  - key_points: 要点数组，每个要点包含：
    - text: 完整陈述（必填）
    - sub_points: 子要点数组（可选，需要时才用）
    - emphasis: "high" / "medium" / "low"（可选，默认 "medium"）
- 封面页（cover）和结束页（ending）不需要 key_points
{page_instruction}

## 输出格式
```json
{{
  "title": "演示文稿标题",
  "slides": [
    {{
      "page": 1,
      "layout": "cover",
      "title": "封面标题",
      "key_points": []
    }},
    {{
      "page": 3,
      "layout": "content",
      "title": "核心论点页",
      "key_points": [
        {{
          "text": "2024年全球 AI 市场规模达到 1840 亿美元",
          "emphasis": "high",
          "sub_points": [
            "同比增长 36.8%，连续三年增速超过 30%",
            "其中生成式 AI 占比从 12% 提升至 28%"
          ]
        }},
        {{
          "text": "企业 AI 采用率从 50% 提升至 72%",
          "emphasis": "medium"
        }},
        {{
          "text": "参考来源：Gartner 2024 报告",
          "emphasis": "low"
        }}
      ]
    }},
    ...
  ]
}}
```

只输出 JSON，不要其他内容。"""


def _materials_section(materials: str = "") -> str:
    if not materials or not materials.strip():
        return ""
    preview = materials[:6000] if len(materials) > 6000 else materials
    return f"## 参考材料\n\n以下是用户上传的参考文档内容，请从中提取关键信息融入大纲：\n\n{preview}\n\n"
