OUTLINE_PROMPT = """请根据以下需求生成一个 PPT 幻灯片大纲。

## 用户需求
{requirements}

## 要求
- 返回严格的 JSON 格式
- 包含 title（演示文稿标题）字段
- 包含 slides 数组，每页包含：
  - page: 页码（从 1 开始）
  - layout: 布局类型，可选值：cover / toc / content / section / ending
  - title: 该页标题
  - key_points: 要点数组（字符串列表，每页 3-5 个要点）
- 封面页（cover）不需要 key_points
- 目录页（toc）列出主要章节
- 结束页（ending）不需要 key_points
- 总页数控制在 {page_count} 页左右
- 内容要有逻辑性，层层递进

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
    ...
  ]
}}
```

只输出 JSON，不要其他内容。"""
