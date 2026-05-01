# PPT-Agent 设计方案

> 通过对话与可选文件上传，AI 驱动的 PowerPoint 演示文稿生成系统。
> 核心路径：LLM 生成 HTML 幻灯片 → 截图嵌入 PPTX（无图像生成模型依赖）。

---

## 1. 架构概览

### 1.1 核心流程

```
用户对话 → [需求讨论] → [深度研究] → [大纲生成] → [风格选择] → [幻灯片生成] → [实时预览] → [手动导出 PPTX]
               tool        async tool      tool          tool        async tool      (iframe)    POST /export
                            (可选)                                   (逐张流式)
```

用户可随时对话、修改、补充，整个流程是**状态机**而非线性管道。研究阶段由 agent 根据主题复杂度自主决定是否调用。

### 1.2 各阶段职责

| 阶段 | 实现方式 | 输入 | 输出 | LLM 调用 |
|------|----------|------|------|----------|
| **需求讨论** | 主 Agent 对话 | 用户消息 | 确认的主题/风格/受众/核心信息 | 0 次（纯对话） |
| **文件上传** | `upload_and_parse` tool | 文件路径 | materials.md | 0 次 |
| **深度研究** | `research_topic` tool | 主题、requirements | research_notes.md | 3+ 次（分析+并发维度研究+综合） |
| **大纲生成** | `generate_outline` tool | 主题、materials、research_notes | outline.json（Pydantic 校验） | 1 次（含重试） |
| **风格选择** | `select_template` tool | 模板名 | style_spec.json | 0 次 |
| **幻灯片生成** | `generate_slides` tool | outline + style_spec | N 个 HTML 文件（逐张流式推送） | N 次（并发） |
| **实时预览** | SSE `slide_generated` 事件 | HTML 文件路径 | 前端 iframe 渲染 | 0 次 |
| **导出** | `POST /export` API | slides/ 目录 | .pptx 文件 | 0 次 |

### 1.3 上下文控制

主 Agent 上下文中**不包含**任何 HTML 内容。所有 tool 的 return 值仅为文件路径或简短确认信息。HTML 通过 `asyncio.as_completed()` 并发写入文件，每完成一张通过 `asyncio.Queue` 推送 `slide_generated` SSE 事件，不经过消息历史。

### 1.4 并发控制

| 阶段 | 配置项 | 默认值 | 实现 |
|------|--------|--------|------|
| 维度研究 | `PPT_AGENT_RESEARCH_CONCURRENCY` | 3 | `asyncio.Semaphore` |
| 幻灯片生成 | `PPT_AGENT_SLIDE_CONCURRENCY` | 3 | `asyncio.Semaphore` |
| PNG 渲染 | `PPT_AGENT_RENDER_CONCURRENCY` | 5 | `asyncio.Semaphore` |

---

## 2. 技术栈

### 2.1 后端

| 组件 | 选型 | 说明 |
|------|------|------|
| **Agent 框架** | LangChain Deep Agents | `create_deep_agent`，内置文件系统、工具调用 |
| **Web 框架** | FastAPI | 异步，未来扩展 API 服务 |
| **HTML 渲染** | Playwright (sync API) | 无头浏览器，截图 HTML → PNG（2x 分辨率），`asyncio.to_thread` 调用 |
| **PPTX 生成** | python-pptx | 纯 Python，截图作为幻灯片背景嵌入 |
| **配置管理** | Pydantic Settings | 环境变量 + .env 文件 |
| **对话持久化** | SQLite (AsyncSqliteSaver) | LangGraph checkpoint 持久化，重启恢复会话 |
| **包管理** | uv | 快速依赖管理与虚拟环境 |

### 2.2 LLM 提供商

通过统一 `get_model()` 工厂函数创建实例：

| 提供商 | model 格式 | 对接方式 |
|--------|-----------|----------|
| Anthropic | `anthropic:claude-sonnet-4-6` | `init_chat_model` |
| OpenAI | `openai:gpt-4o` | `init_chat_model` |
| OpenRouter | `openrouter:google/gemini-2.5-flash` | `ChatOpenAI(base_url=...)` |
| 智谱 | `zhipu:glm-4` | `ChatOpenAI(base_url=...)` |
| VLLM | `vllm:model-name` | `ChatOpenAI(base_url=...)` |

### 2.3 前端

| 组件 | 选型 |
|------|------|
| 框架 | Vue 3 + TypeScript |
| 构建 | Vite |
| 状态管理 | Pinia |
| HTTP 客户端 | axios |
| Markdown | marked + DOMPurify |
| 样式 | CSS (scoped) + CSS Variables 设计系统 |

---

## 3. Deep Agents 架构

### 3.1 Agent 定义

```python
agent = create_deep_agent(
    model=get_model(),
    system_prompt=SYSTEM_PROMPT,
    tools=[
        research_topic,        # 深度研究（3 步 LLM，可选）
        generate_outline,      # 大纲生成（含重试 + Pydantic 校验）
        select_template,       # 模板选择
        list_templates,        # 查看模板列表
        generate_slides,       # 幻灯片并发生成
        export_pptx,           # PPTX 导出
        upload_and_parse,      # 文件上传解析（markitdown）
    ],
    checkpointer=AsyncSqliteSaver.from_conn_string("output/checkpoints.db"),
    backend=FilesystemBackend(root_dir="output"),
)
```

所有 tool 均为 `async`，在单一 event loop 中运行。

### 3.2 主 Agent Tools

| Tool | 触发时机 | 输出 | 副作用 |
|------|----------|------|--------|
| `upload_and_parse` | 用户上传文件 | 解析确认 + 内容预览 | 保存 materials.md，注入 HumanMessage 到对话 |
| `research_topic` | 主题确认后，复杂主题时 Agent 自主调用 | 研究完成确认 | 保存 research_notes.md，更新 session.json |
| `generate_outline` | 主题确认后（研究后如有） | 大纲 JSON（NarrativeFramework + SupportingPoint 结构） | 保存 outline.json，更新 session.json |
| `select_template` | 大纲确认后 | 简短确认 | 保存 style_spec.json，更新 session.json |
| `list_templates` | 用户主动要求 | 模板列表 | 无 |
| `generate_slides` | 模板确认后 | 文件路径列表 + 失败警告 | 逐张并发 LLM 调用，每完成一张推送 slide_generated 事件，保存 HTML |
| `export_pptx` | 禁止 AI 调用 | PPTX 路径 + 失败警告 | 仅用户手动触发（POST /export），并发截图 |

### 3.3 配置

```python
class Settings(BaseSettings):
    model: str = "anthropic:claude-sonnet-4-6"
    output_dir: Path = Path("./output")
    vllm_base_url: str = ""
    vllm_api_key: str = "empty"
    zhipu_base_url: str = "https://open.bigmodel.cn/api/paas/v4"
    zhipu_api_key: str = ""
    slide_concurrency: int = 3
    render_concurrency: int = 5
    research_concurrency: int = 3
```

---

## 4. 会话状态机

### 4.1 PipelineStep 枚举

```
IDLE → TEMPLATE_DONE → RESEARCH_DONE → OUTLINE_DONE → SLIDES_DONE → EXPORTED
```

### 4.2 SessionState 结构

```python
class SessionState(BaseModel):
    session_id: str
    step: PipelineStep
    title: str
    outline_file: str
    style_spec_file: str
    slides_dir: str
    pptx_file: str
    template_key: str
    research_file: str = ""
    created_at: str
```

每次 tool 执行后更新 `session.json`，确保各 tool 间的数据流转有据可查，不依赖隐式文件命名约定。

### 4.3 SessionIndex（会话索引）

```python
class SessionEntry(BaseModel):
    session_id: str
    title: str
    step: PipelineStep
    template_key: str
    created_at: str
```

所有会话记录在 `output/index.json` 中，前端可通过 `SessionIndex.list_all()` 获取完整列表。

### 4.4 大纲校验

```python
class Evidence(BaseModel):
    claim: str
    evidence_type: Literal["data", "case_study", "quote", "analysis", "analogy"]
    detail: str = ""
    source: str = ""

class SupportingPoint(BaseModel):
    message: str
    evidence: list[Evidence] = []

class NarrativeFramework(BaseModel):
    framework: Literal["scqa", "problem_solution", "chronological", "custom"] = "scqa"
    situation: str = ""
    complication: str = ""
    core_question: str = ""
    core_answer: str = ""

class SlideItem(BaseModel):
    page: int = Field(ge=1)
    layout: Literal["cover", "toc", "content", "section", "ending"]
    headline: str                                  # Action Title，完整陈述句
    body_text: str = ""
    supporting_points: list[SupportingPoint] = []
    speaker_notes: str = ""
    section: str = ""                             # narrative role: situation/complication/...
    visual_hint: str = ""                         # table / comparison / timeline / process / chart / quote_highlight

class Outline(BaseModel):
    title: str
    slides: list[SlideItem]  # 不能为空
    audience: str = ""
    objective: Literal["persuade", "report", "educate", "inspire"] = "report"
    narrative: NarrativeFramework = Field(default_factory=NarrativeFramework)
```

`SlideItem.headline` 使用 Action Title 模式（完整陈述句而非主题标签），`SupportingPoint` + `Evidence` 提供论据层次结构（含证据类型标注）。`NarrativeFramework` 支持 SCQA 等叙事框架，为演示文稿提供叙事线索。

重试时将 `ValidationError` 的具体错误信息反馈给 LLM，提高修复率。

---

## 5. HTML 幻灯片规范

### 5.1 画布规格

```
尺寸：1280 × 720 px（16:9）
字体：'Microsoft YaHei', 'PingFang SC', sans-serif
渲染：Playwright Chromium，viewport 1280×720，device_scale_factor=2
```

### 5.2 骨架模板（Skeleton）

幻灯片生成采用**骨架 + 内容分离**架构：

- **骨架（Skeleton）**：每种布局类型的 HTML 骨架定义固定的页面结构（header、content 区域、footer/页码），style_spec 的配色/字体通过 `{{var}}` 占位符注入
- **内容区域**：LLM 只生成 `<div class="slide-content">` 内部的 HTML 片段
- **合并**：`render_skeleton()` 将骨架、style_spec、LLM 内容合并为完整 HTML

骨架加载优先级：模板特定骨架（`{template}/skeletons/{layout}.html`）> 共享骨架（`skeletons/{layout}.html`）

骨架保证的**跨页一致性**：
- 页码固定在右下角（`N / M` 格式）
- headline 位置和样式统一
- CSS reset + 基础字体在骨架中定义
- style_spec 精确映射为 CSS 值
- `:root` CSS 变量块：9 个主题色变量（`--primary`、`--secondary`、`--accent`、`--accent-2`、`--bg`、`--card-bg`、`--text`、`--text-light`、`--border`），LLM 通过 `var(--xxx)` 引用模板色值，自动适配深色/浅色模板

### 5.3 Style Spec 结构

每个模板包含 `style_spec.json`，定义配色、字体、间距、组件样式、**三级强调样式**。

```json
{
  "emphasis": {
    "high": { "font_size": "24px", "color": "#ed8936", "font_weight": "bold" },
    "medium": { "font_size": "20px", "color": "#2d3748", "font_weight": "normal" },
    "low": { "font_size": "16px", "color": "#a0aec0", "font_weight": "normal" }
  },
  "component_styles": {
    "content": "白色背景，顶部蓝色标题栏，要点列表使用灰色圆点，左侧可留蓝色边框装饰",
    "cover": "深蓝色背景，白色大标题居中，底部橙色装饰线"
  }
}
```

`component_styles`（per-layout 视觉指导）和 `emphasis`（三级强调：字号/颜色/字重/发光效果）在幻灯片生成时注入 LLM prompt，确保生成内容遵循模板风格。`render_skeleton()` 的 `style_map` 将 `accent_2`、`card_bg`、`border_color` 等扩展字段映射到 CSS 变量，LLM 通过 `var(--card-bg)` 等引用。

### 5.4 布局类型

`cover` / `toc` / `content` / `section` / `ending`

### 5.5 视觉元素提示（visual_hint）

SlideItem 的 `visual_hint` 字段指导内容区域的渲染方式：
- `table`：数据对比表格
- `comparison`：左右对比布局
- `timeline`：时间线
- `process`：流程图
- `chart`：CSS 图表
- `quote_highlight`：金句突出展示
- 留空：默认列表布局

---

## 6. 联网搜索

研究阶段可选的联网增强，为每个研究维度提供实时 Web 内容。

### 6.1 架构

```
SearchProvider (Protocol)
├── TavilySearchProvider   (httpx + Tavily REST API)
└── BrowserSearchProvider  (Playwright，后续支持)
```

搜索不是独立的 agent tool，而是 `research_topic` 内部的增强。Agent 不感知搜索的存在，只感知研究质量提升。

### 6.2 集成流程

`_step2_research_dimension` 中，LLM 调用前：
1. 从 dimension 的 `search_queries`（LLM 在分析阶段预生成的搜索词）取第一个查询
2. 调用 `SearchProvider.search(query)` 获取结果
3. 通过 `_search_results_section()` 注入 `RESEARCH_DIMENSION_PROMPT` 的 `{search_section}` 占位符，提示 LLM 优先使用搜索事实
4. 搜索失败不阻断研究（try/except 静默降级为纯 LLM）

### 6.3 配置

| 环境变量 | 默认值 | 说明 |
|--------|--------|------|
| `PPT_AGENT_SEARCH_PROVIDER` | `""` | `"tavily"` 启用，留空禁用 |
| `PPT_AGENT_TAVILY_API_KEY` | `""` | Tavily API Key |

---

## 7. 导出管线

```
HTML → Playwright 截图(2x, 并发) → PNG → python-pptx 嵌入 → .pptx
```

- **Sync API + `asyncio.to_thread()`**：使用同步 Playwright 避免与 uvicorn 的事件循环冲突（Windows 兼容）
- 浏览器实例复用：`threading.local()` 在渲染线程中保持单一浏览器实例
- 并发控制：`Semaphore(5)` 限制同时发起的渲染线程数
- 截图分辨率：2560×1440（2x 缩放）

---

## 8. 项目结构

```
ppt-agent/
├── pyproject.toml
├── .env.example
│
├── src/ppt_agent/
│   ├── main.py                 # CLI 入口（会话隔离 + contextvar）
│   ├── config.py               # Pydantic Settings + 并发配置 + 会话目录 contextvar
│   ├── progress.py             # 逐张幻灯片进度队列（模块级 dict，session_id → asyncio.Queue）
│   ├── llm.py                  # get_model() 工厂函数
│   │
│   ├── agent/
│   │   ├── agent.py            # create_deep_agent 定义
│   │   ├── prompts.py          # 主 Agent 系统提示词
│   │   ├── subagents.py        # （保留备用）
│   │   └── state.py            # Evidence + SupportingPoint + NarrativeFramework + Outline + SessionState + PipelineStep
│   │
│   ├── tools/
│   │   ├── research.py         # research_topic（3 步 LLM 分析+并发维度研究+综合，可选联网搜索）
│   │   ├── outline.py          # generate_outline（Pydantic 校验 + 重试 + materials + research_notes）
│   │   ├── template.py         # select_template / list_templates
│   │   ├── slide_gen.py        # generate_slides（as_completed 逐张生成 + 进度队列推送 + 容错）
│   │   ├── export.py           # do_export（核心导出逻辑）+ export_pptx tool（手动触发）
│   │   └── upload.py           # upload_and_parse（markitdown 文档解析）
│   │
│   ├── search.py               # SearchProvider 协议 + Tavily 实现（研究阶段联网搜索）
│   ├── templates/
│   │   ├── registry.py         # 模板查询 + 骨架加载 + 渲染合并
│   │   ├── skeletons/          # 共享 HTML 骨架（cover/toc/content/section/ending）
│   │   ├── simple_business/
│   │   ├── tech_dark/
│   │   ├── education/
│   │   ├── creative/
│   │   ├── report/
│   │   ├── thesis_defense/
│   │   ├── sunset/
│   │   ├── chinese_ink/
│   │   └── cyberpunk/
│   │
│   ├── export/
│   │   ├── renderer.py         # Playwright sync API（thread-local 浏览器复用）
│   │   └── pptx_builder.py     # python-pptx 组装
│   │
│   ├── prompts/
│   │   ├── research.py          # 研究提示词（分析+维度研究+综合）
│   │   ├── outline.py
│   │   ├── slide.py
│   │   └── style.py
│   │
│   └── api/
│       ├── app.py               # FastAPI 应用 + CORS + 中间件
│       ├── server.py            # uvicorn 启动入口
│       ├── deps.py              # 依赖注入（agent 单例）
│       ├── streaming.py         # SSE 流式生成器（后台 agent 任务 + 进度队列并发读取）
│       └── routes/
│           ├── sessions.py      # 会话 CRUD + 消息 + 上传 + 下载 + 导出 + 单张重试 + 幻灯片预览（CSP） + 研究笔记查询
│           ├── templates.py     # 模板查询
│           └── upload.py        # 文件上传处理
│
└── tests/
    ├── test_tools.py           # 41 个测试（模板、工具、校验、状态、会话索引、上传、研究、骨架）
    └── test_renderer.py        # 渲染和 PPTX 管线测试
```

### 7.2 前端项目结构

```
web/
├── src/
│   ├── api/
│   │   ├── client.ts            # axios 实例
│   │   └── types.ts             # TypeScript 类型定义
│   ├── stores/
│   │   ├── sessions.ts          # 会话列表 store
│   │   └── session.ts           # 单会话 store（SSE 流处理 + pipeline step）
│   ├── components/
│   │   ├── App.vue              # 根组件（欢迎屏）
│   │   ├── ChatInterface.vue    # 对话主界面（编排器）
│   │   ├── SessionList.vue      # 侧边栏会话列表
│   │   ├── MessageList.vue      # 消息列表（Markdown + DOMPurify + 工具卡片）
│   │   ├── InputBar.vue         # 输入栏
│   │   ├── FileUpload.vue       # 文件上传（拖拽）
│   │   ├── PipelineStepper.vue  # 6 步流程进度条（含研究步骤）
│   │   ├── OutlinePreview.vue   # 大纲结构化展示（SCQA + headline + evidence）
│   │   ├── ResearchPreview.vue  # 研究笔记折叠展示卡片
│   │   ├── TemplateSelector.vue # 模板选择器
│   │   ├── TemplateCard.vue     # 模板预览卡片（渐变色条）
│   │   ├── TemplateLibrary.vue  # 模板库模态框（Teleport，侧边栏入口）
│   │   └── SlidePreview.vue     # 幻灯片预览（iframe + CSS transform 缩略图 + 单张重试）
│   └── styles/
│       └── main.css             # CSS Variables 设计系统
└── package.json
```

---

## 9. MVP 状态

### 8.1 已完成

- [x] CLI 对话入口（单 event loop，async）
- [x] 7 阶段完整流程（含文件上传 + 深度研究）
- [x] 7 个 async Tools
- [x] 深度研究（research_topic：3 步 LLM 分析→并发维度研究→综合，Agent 自主决定是否调用）
- [x] 并发幻灯片生成（Semaphore 控制并发数 + return_exceptions 容错）
- [x] 逐张流式渲染（asyncio.as_completed + asyncio.Queue + SSE slide_generated 事件）
- [x] iframe 实时预览（CSS transform 缩放缩略图 + sandbox + CSP 安全头）
- [x] 手动导出（Agent 不自动调用 export_pptx，用户界面点击导出按钮）
- [x] 单张幻灯片重试（备份/恢复机制，cache busting 刷新 iframe）
- [x] 模板库（侧边栏入口，Teleport 模态框，渐变色条 + 调色板预览）
- [x] 并发 PNG 渲染（浏览器复用 + Semaphore + 容错）
- [x] 9 个预设模板
- [x] Playwright 2x 截图 + python-pptx 导出
- [x] 4 个 LLM 提供商
- [x] Outline Pydantic 校验 + 结构化重试
- [x] SCQA 叙事框架 + Action Title + Evidence 论据结构
- [x] NarrativeFramework（SCQA/问题-方案/时间线/自定义）
- [x] Evidence 类型标注（data/case_study/quote/analysis/analogy）
- [x] visual_hint 视觉元素提示（table/comparison/timeline/process/chart/quote_highlight）
- [x] 骨架模板架构（Skeleton + 内容分离，页面结构一致性保证）
- [x] 页数自适应（LLM 根据内容复杂度决定页数，或用户指定）
- [x] SessionState 状态机（损坏文件自动回退）
- [x] 会话隔离（每次生成独立目录，contextvars 传递会话上下文）
- [x] SessionIndex 会话索引（index.json，前端可读取列表）
- [x] 三级强调样式（模板 emphasis 定义）
- [x] 文件上传与解析（markitdown：docx/xlsx/pdf/html/图片等，20MB 限制）
- [x] 参考材料融入大纲（materials.md 自动读取 + materials 参数传递）
- [x] 研究笔记融入大纲（research_notes.md 自动读取 + research section 注入）
- [x] 容错机制（单页生成失败不影响整体、HTML 有效性校验、PPTX 嵌入异常跳过、GraphInterrupt 恢复）
- [x] 56 个单元测试
- [x] Debug 输出（TOOL 调用/结果追踪）

### 8.2 API 服务器

- [x] FastAPI 应用（CORS + 中间件）
- [x] SSE 流式对话
- [x] 会话管理（CRUD）
- [x] 文件上传（multipart）
- [x] PPTX 下载
- [x] 模板查询
- [x] 会话上下文中间件（从 URL 提取 session_id）
- [x] SQLite 对话持久化（AsyncSqliteSaver，重启恢复）
- [x] 历史消息加载（GET /sessions/{id} 返回 checkpointer 历史）

### 8.3 前端界面

- [x] Vue 3 + TypeScript 项目结构
- [x] Pinia 状态管理（sessions store + per-session store 工厂模式）
- [x] SSE 实时流式展示（含缓冲区 flush）
- [x] Markdown 渲染（marked + DOMPurify 防 XSS）
- [x] 文件上传（drag & drop）
- [x] 会话管理（创建、列表、删除、切换）
- [x] 会话历史恢复（从 SQLite checkpointer 加载历史消息 + 大纲恢复）
- [x] CSS Variables 设计系统（spacing、radius、shadow、状态色、transition）
- [x] 6 步流程进度条（PipelineStepper：SSE tool_result 实时映射，含研究步骤）
- [x] 大纲结构化展示（OutlinePreview：SCQA narrative + headline + supporting_points + evidence badges）
- [x] 研究笔记折叠展示（ResearchPreview：marked + DOMPurify 渲染，可折叠）
- [x] 浏览器标签栏通知（Notification API + document.title 闪烁，tool 完成时提醒用户）
- [x] 模板选择卡片（TemplateCard：渐变色条预览 + TemplateSelector 水平滚动）
- [x] 幻灯片 iframe 实时预览（SlidePreview：逐张流式渲染 + CSS transform 缩略图 + 点击放大 + 单张重试）
- [x] 模板库（TemplateLibrary：侧边栏入口 + Teleport 模态框 + 渐变色条 + 调色板预览）
- [x] 手动导出按钮（slides_done 步骤显示"导出 PPTX"，exported 步骤显示"下载 PPTX"）
- [x] 工具调用状态卡片（进行中旋转图标 + 完成勾选图标 + 描述文本）
- [x] 空状态欢迎屏（品牌图标 + 推荐提示词 chips）
- [x] 响应式设计

### 8.4 待开发

- [x] 联网搜索（Tavily，SearchProvider 可扩展架构）
- [x] 浏览器搜索（Playwright 操作浏览器，基于 SearchProvider 扩展）
- [ ] AI 自定义风格生成

---

## 10. 关键设计决策记录

### 9.1 async tool 并发而非子代理

**选择**：幻灯片生成作为 async tool + `asyncio.gather()` 并发，不使用子代理。
**原因**：tool 返回值只有文件路径，HTML 不进主 Agent 上下文，等效于子代理隔离。同时支持并发，子代理无法内部并发。两者上下文隔离效果相同。

### 9.2 SessionState 显式状态机

**选择**：每次 tool 执行后更新 `session.json`，用 `PipelineStep` 枚举跟踪进度。
**原因**：替代隐式文件命名约定（"generate_outline 写 outline.json，下一个 tool 自己去读"），工具间协作有据可查，便于调试和错误恢复。

### 9.3 Pydantic 校验大纲

**选择**：`Outline` + `SlideItem` Pydantic model 校验大纲结构。
**原因**：LLM 返回的 JSON 不可靠，可能缺少字段、layout 值非法、slides 为空。结构化校验在写入文件前拦截，错误信息反馈给 LLM 提高重试成功率。

### 9.4 Semaphore 并发控制

**选择**：`asyncio.Semaphore` 限制 LLM 调用和 Playwright 截图的并发数。
**原因**：无限制并发会触发 API 速率限制或内存暴涨。可配置的并发数适应不同提供商的限流策略。

### 9.5 HTML 而非 SVG/Canvas

**选择**：每张幻灯片生成完整 HTML 文件。
**原因**：HTML 生态最成熟，CSS 布局灵活，字体支持好，Playwright 渲染稳定。

### 9.6 截图嵌入而非原生 PPTX 对象

**选择**：HTML → PNG 截图 → 作为背景嵌入 PPTX。
**原因**：python-pptx 原生形状能力有限，无法还原复杂 CSS 布局。截图保证像素级还原。

### 9.7 OpenAI 兼容接口统一多提供商

**选择**：智谱和 VLLM 均通过 `ChatOpenAI(base_url=...)` 对接。
**原因**：一套 SDK 覆盖所有提供商，减少维护成本。

### 9.8 浏览器实例复用

**选择**：`browser_context()` 上下文管理器，一次启动 Chromium 供所有截图复用。
**原因**：每次启动浏览器约 1-2 秒，N 页 PPT 串行启动 N 次是性能瓶颈。

### 9.9 会话隔离（contextvars + 独立目录）

**选择**：每次 PPT 生成创建独立目录 `output/{session_id}/`，通过 `contextvars.ContextVar` 传递当前会话目录，tools 用 `get_session_dir()` 读取。
**原因**：防止不同 PPT 生成之间的内容泄露（对话历史、文件残留），同时保留所有历史记录供前端展示。`contextvars` 是 async 安全的，不改变 tool 签名，main.py 在每次 agent 调用前设置。

### 9.10 会话上下文传播（URL 解析 + SSE generator 显式设置）

**选择**：API 中间件从 URL 路径手动提取 `session_id`（`/api/v1/sessions/{session_id}/...`），在 SSE 流式生成器中显式设置 `_current_session_dir` contextvar。
**原因**：FastAPI 中间件在路由匹配之前执行，`request.path_params` 此时为空。异步 generator 中 contextvar 不会自动传播，必须在 agent 调用前显式设置并在 finally 中重置。

### 9.11 SCQA 叙事框架 + Action Title + Evidence 结构

**选择**：大纲数据模型从 `KeyPoint` 重构为 `NarrativeFramework` + `SupportingPoint` + `Evidence` 三层结构，slide `title` 改为 `headline`（Action Title 模式）。
**原因**：旧 `KeyPoint` 结构过于扁平，缺少叙事线索和论据层次。SCQA（Situation→Complication→Question→Answer）框架为演示提供叙事主线。Action Title 要求每页标题是完整陈述句而非主题标签（参考 McKinsey 金字塔原理）。Evidence 支持多种证据类型（data/case_study/quote/analysis/analogy），提升内容说服力。不做向后兼容，旧 KeyPoint 结构直接废弃。

### 9.12 Agent 主动收集内容素材

**选择**：主 Agent 确认主题时，在一轮对话中同时收集受众、核心信息、数据/案例。
**原因**：即使后续支持文件上传和联网搜索，用户也可能只输入一个简短主题。Agent 主动收集素材是大纲质量的基础，与搜索/上传功能互补不冲突。

### 9.13 文件上传独立 tool + materials.md

**选择**：`upload_and_parse` 作为独立 tool，解析结果保存为 `materials.md`，`generate_outline` 通过 `materials` 参数独立读取。
**原因**：模块间更独立，upload 和 outline 解耦。支持多文件上传追加到同一 materials.md。大纲生成自动从会话目录读取 materials.md，也可通过参数直接传入。

### 9.14 asyncio.gather return_exceptions 容错

**选择**：幻灯片生成和渲染的 `asyncio.gather()` 均使用 `return_exceptions=True`，捕获异常后跳过失败项并报告。
**原因**：N 页 PPT 中单页 LLM 调用失败（限流、超时、格式错误）或渲染失败（浏览器崩溃）不应导致整体崩溃。失败信息汇总返回给用户，方便定位问题。

### 9.15 平衡花括号匹配提取 JSON

**选择**：`_extract_json` 的回退方案使用平衡花括号计数，替代贪婪正则 `r"\{.*\}"`。
**原因**：贪婪正则会从第一个 `{` 匹配到最后一个 `}`，LLM 返回 JSON 前后的解释文本中包含花括号时会导致匹配范围错误。平衡匹配更精确，同时正确处理 JSON 字符串内的转义花括号。

### 9.16 SQLite 持久化对话历史

**选择**：`AsyncSqliteSaver` 替代 `MemorySaver`，checkpoint 存储在 `output/checkpoints.db`。
**原因**：MemorySaver 仅内存驻留，进程退出后对话历史全部丢失。SQLite 持久化后，CLI/API 重启可恢复历史会话，前端通过 `GET /sessions/{id}` 从 checkpointer 读取消息并展示。

### 9.17 Playwright Sync API + asyncio.to_thread

**选择**：使用 `playwright.sync_api` + `asyncio.to_thread()` 替代 `playwright.async_api`。
**原因**：uvicorn 在 Windows 上使用 `SelectorEventLoop`（不支持 `asyncio.create_subprocess_exec`），而 Playwright async API 内部依赖子进程启动浏览器。同步 API 使用 `subprocess.Popen`（不受此限制），通过 `asyncio.to_thread` 在线程池中运行，完全兼容 uvicorn 的事件循环。浏览器实例通过 `threading.local()` 在渲染线程中复用。

### 9.18 上传文件注入 Agent 对话

**选择**：CLI 的 `/upload` 命令在解析文件后，将结果作为 `HumanMessage` 注入 agent 对话。
**原因**：之前 `/upload` 只在控制台打印结果就 `continue`，agent 的 LangGraph 对话历史中没有上传记录，导致 agent 不知道用户上传了材料。注入后 agent 能感知上传内容，配合系统提示词中的上传指引，正确调用 `generate_outline`（自动读取 `materials.md`）。

### 9.19 研究阶段独立 Tool + research_notes.md

**选择**：`research_topic` 作为独立 tool，3 步内部 LLM 调用（分析→并发维度研究→综合），产出 `research_notes.md`。接受 `audience` 和 `objective` 参数，贯穿三个阶段聚焦内容方向。
**原因**：研究阶段与大纲生成分离，agent 根据主题复杂度自主决定是否调用。3 步设计确保研究深度：先分析确定维度（MECE），再并发研究各维度，最后综合为结构化笔记。`research_notes.md` 作为 `generate_outline` 的输入素材，与 `materials.md` 模式一致。

研究 prompt 改进：
- 主题类型感知（商业分析/技术方案/说服提案/知识教育），维度设计参考对应默认结构
- 维度 3-5 个（MECE），每个附带 2 个预生成的 `search_queries`（具体关键词 + 年份）
- 信息可靠性分级：`[已验证]`/`[行业共识]`/`[分析推断]`/`[待验证]`
- 综合阶段主动检测矛盾、标注知识空白、建议 SCQA 叙事框架 + PPT 映射

大纲 prompt 改进：
- 主题类型检测 + 默认参考结构（商业分析/技术方案/说服提案/知识教育各一套）
- `_time_hint()` 注入当前日期，避免 LLM 时间盲区
- 少样本示例（远程办公主题），展示 Action Title、SCQA、evidence、section 页的正确用法
- 5 项自查清单（headline/递进/论据/visual_hint/section 页）
- section 页和 body_text 的使用规则

幻灯片 prompt 改进：
- `:root` CSS 变量（9 个）替代硬编码颜色，LLM 通过 `var(--xxx)` 自动适配深色/浅色模板
- `component_styles`（per-layout 视觉指导）和 `emphasis`（三级强调）从 style_spec 注入 prompt
- 6 种 visual_hint 的参考 HTML 代码片段（table/comparison/timeline/process/chart/quote_highlight）
- evidence_type 渲染示例（data 加粗/quote blockquote/case_study 斜体等）
- 内容密度指南（1120×480px 可用空间，按要点数量建议字号）
- 反模式禁止列表（absolute 定位、硬编码宽度、自选颜色、外部资源）

### 9.20 浏览器标签栏通知

**选择**：tool 完成时通过 Notification API 发送系统通知 + `document.title` 闪烁提醒用户。
**原因**：PPT 生成耗时较长（研究 30-60s，幻灯片生成数分钟），用户可能切换到其他标签页。Notification API 提供系统级通知（需用户授权），`document.title` 闪烁作为降级方案（1 秒间隔交替显示，10 秒自动停止，用户切回标签页时立即停止）。两种方式互补，确保用户不错过关键节点（研究完成、大纲生成、导就绪）。

### 9.21 骨架模板 + 内容分离架构

**选择**：预定义 5 种布局的 HTML 骨架（cover/toc/content/section/ending），LLM 只生成内容区域 HTML，`render_skeleton()` 合并骨架 + style_spec + 内容。
**原因**：每页由 LLM 独立生成，完全自由的输出导致页码位置不一致、headline 样式不一。骨架固定 header（headline）、footer（右下角页码）、CSS reset，确保跨页一致性。模板可覆盖 `skeletons/{layout}.html` 实现自定义布局。

### 9.22 逐张流式渲染（asyncio.Queue + SSE）

**选择**：`generate_slides` 使用 `asyncio.as_completed()` 替代 `asyncio.gather()`，每完成一张幻灯片通过模块级 `dict[str, asyncio.Queue]`（`progress.py`）推送 `slide_generated` 事件。SSE generator 在后台运行 `ainvoke()`，主循环 `asyncio.wait_for(queue.get())` 实时读取进度事件。
**原因**：`ainvoke()` 阻塞到所有工具完成才返回，无法中途推送事件。后台任务 + Queue 方案在保持 agent 调用方式不变的同时实现逐张推送。使用模块级 dict 而非 ContextVar 避免在 LangGraph 内部 task 创建时 context 丢失。

### 9.23 手动导出取代自动导出

**选择**：Agent prompt 改为"禁止调用 export_pptx"，新增 `POST /sessions/{id}/export` API 端点直接调用 `do_export()`。前端在 `slides_done` 步骤显示"导出 PPTX"按钮。
**原因**：用户在导出前无法审查幻灯片效果，导出后发现问题只能重新生成。手动导出让用户先预览确认，不满意可修改或重试单张后再导出。提取 `do_export()` 为独立函数供 API 和 tool 共用。

### 9.24 iframe 预览安全（CSP + sandbox）

**选择**：幻灯片 HTML 通过 `<iframe>` 直接渲染预览，使用 `sandbox=""`（禁止脚本）+ CSP `default-src 'none'; style-src 'unsafe-inline'; img-src data:;` 安全头。
**原因**：幻灯片 HTML 由 LLM 生成，可能包含恶意 JavaScript。`sandbox=""` 阻止所有脚本执行和同源访问，CSP 进一步限制资源加载。缩略图使用 CSS `transform: scale(0.109)` 将 1280×720 iframe 缩放为 140px 宽。

### 9.25 单张重试（备份/恢复）

**选择**：`POST /sessions/{id}/slides/{page}/retry` 端点，重试前将原 HTML 备份为 `.html.bak`，成功后删除备份，失败则恢复。
**原因**：重试可能失败（LLM 错误、无效 HTML），无备份会导致原幻灯片丢失。前端通过 `:key` 包含版本号强制 Vue 销毁重建 iframe，配合 `?v=N` cache bust 确保加载新内容。

### 9.26 PlaywrightSearchProvider 浏览器搜索

**选择**：基于 Playwright async API 实现 `PlaywrightSearchProvider`，通过操作 Bing 搜索引擎获取结果并抓取页面内容。
**原因**：Tavily 等 API 需要付费密钥，且无法控制搜索源。浏览器搜索零成本，可访问任何网站，支持中文搜索。使用 `SearchProvider` 协议保持架构一致，`get_search_provider()` 根据 `PPT_AGENT_SEARCH_PROVIDER` 配置返回对应实现。

**关键设计**：
- 浏览器实例生命周期：Provider 级别共享，`asyncio.Lock` 保护懒启动，`aclose()` 显式关闭
- SERP 解析：Bing `.b_algo` 选择器提取标题、URL、摘要，降级到 SERP snippet 作为 fallback
- 内容提取：Playwright `wait_until="networkidle"` 等 JS 渲染 → `page.content()` → trafilatura 提取正文
- 去重与过滤：域名去重、URL 后缀过滤非 HTML 资源、< 200 字内容标记无效
- 反爬：隐藏 `navigator.webdriver`、真实 User-Agent 池、随机延迟（0.5-1.5s）
- 超时控制：Bing 搜索 15s、页面加载 10s，超时跳过

---

## 11. 已修复问题

### 10.1 研究后自动跳转到大纲生成 ✅ 已修复

- `research_topic` 返回值增加维度名称 + 研究笔记摘要预览（800 字）
- Agent prompt 强化"必须展示摘要并等待用户确认后再调用 generate_outline"

### 10.2 生成大纲内容质量不稳定 ✅ 已修复

- 大纲 prompt 增加"第三步：自查"，要求 LLM 逐页检查 headline 是否为结论句、页面间是否有逻辑递进、visual_hint 是否合理使用

### 10.3 前端历史对话状态显示为"未开始" ✅ 已修复

- 新增 `sync_session_index()` 函数，每个 tool 更新 `session.json` 后同步更新 `index.json`
- `SessionList.vue` 的 `STEP_LABELS` 补充 `research_done: "研究完成"`

### 10.4 历史会话列表标题为 session_id ✅ 已修复

- `generate_outline` 完成后调用 `sync_session_index()` 更新 `index.json` 中的 title 和 step
- 侧边栏现在显示 PPT 标题而非 session_id
