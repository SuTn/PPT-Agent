# PPT-Agent 设计方案

> 通过对话与可选文件上传，AI 驱动的 PowerPoint 演示文稿生成系统。
> 核心路径：LLM 生成 HTML 幻灯片 → 截图嵌入 PPTX（无图像生成模型依赖）。

---

## 1. 架构概览

### 1.1 核心流程

```
用户对话 → [需求讨论] → [大纲生成] → [风格选择] → [幻灯片生成] → [导出 PPTX]
               tool           tool          tool        async tool         async tool
```

用户可随时对话、修改、补充，整个流程是**状态机**而非线性管道。

### 1.2 各阶段职责

| 阶段 | 实现方式 | 输入 | 输出 | LLM 调用 |
|------|----------|------|------|----------|
| **需求讨论** | 主 Agent 对话 | 用户消息 | 确认的主题/风格/受众/核心信息 | 0 次（纯对话） |
| **文件上传** | `upload_and_parse` tool | 文件路径 | materials.md | 0 次 |
| **大纲生成** | `generate_outline` tool | 主题、materials | outline.json（Pydantic 校验） | 1 次（含重试） |
| **风格选择** | `select_template` tool | 模板名 | style_spec.json | 0 次 |
| **幻灯片生成** | `generate_slides` tool | outline + style_spec | N 个 HTML 文件 | N 次（并发） |
| **导出** | `export_pptx` tool | slides/ 目录 | .pptx 文件 | 0 次 |

### 1.3 上下文控制

主 Agent 上下文中**不包含**任何 HTML 内容。所有 tool 的 return 值仅为文件路径或简短确认信息。HTML 通过 `asyncio.gather()` 并发写入文件，不经过消息历史。

### 1.4 并发控制

| 阶段 | 配置项 | 默认值 | 实现 |
|------|--------|--------|------|
| 幻灯片生成 | `PPT_AGENT_SLIDE_CONCURRENCY` | 3 | `asyncio.Semaphore` |
| PNG 渲染 | `PPT_AGENT_RENDER_CONCURRENCY` | 5 | `asyncio.Semaphore` |

---

## 2. 技术栈

### 2.1 后端

| 组件 | 选型 | 说明 |
|------|------|------|
| **Agent 框架** | LangChain Deep Agents | `create_deep_agent`，内置文件系统、工具调用 |
| **Web 框架** | FastAPI | 异步，未来扩展 API 服务 |
| **HTML 渲染** | Playwright | 无头浏览器，截图 HTML → PNG（2x 分辨率） |
| **PPTX 生成** | python-pptx | 纯 Python，截图作为幻灯片背景嵌入 |
| **配置管理** | Pydantic Settings | 环境变量 + .env 文件 |
| **包管理** | uv | 快速依赖管理与虚拟环境 |

### 2.2 LLM 提供商

通过统一 `get_model()` 工厂函数创建实例：

| 提供商 | model 格式 | 对接方式 |
|--------|-----------|----------|
| Anthropic | `anthropic:claude-sonnet-4-6` | `init_chat_model` |
| OpenAI | `openai:gpt-4o` | `init_chat_model` |
| 智谱 | `zhipu:glm-4` | `ChatOpenAI(base_url=...)` |
| VLLM | `vllm:model-name` | `ChatOpenAI(base_url=...)` |

### 2.3 前端

| 组件 | 选型 |
|------|------|
| 框架 | Vue 3 + TypeScript |
| 构建 | Vite |
| 状态管理 | Pinia |
| HTTP 客户端 | axios |
| Markdown | marked |
| 样式 | CSS (scoped) |

---

## 3. Deep Agents 架构

### 3.1 Agent 定义

```python
agent = create_deep_agent(
    model=get_model(),
    system_prompt=SYSTEM_PROMPT,
    tools=[
        generate_outline,      # 大纲生成（含重试 + Pydantic 校验）
        select_template,       # 模板选择
        list_templates,        # 查看模板列表
        generate_slides,       # 幻灯片并发生成
        export_pptx,           # PPTX 导出
        upload_and_parse,      # 文件上传解析（markitdown）
    ],
    checkpointer=MemorySaver(),
    backend=FilesystemBackend(root_dir="output"),
)
```

所有 tool 均为 `async`，在单一 event loop 中运行。

### 3.2 主 Agent Tools

| Tool | 触发时机 | 输出 | 副作用 |
|------|----------|------|--------|
| `upload_and_parse` | 用户上传文件 | 解析确认 + 内容预览 | 保存 materials.md |
| `generate_outline` | 主题确认后 | 大纲 JSON（KeyPoint 结构） | 保存 outline.json，更新 session.json |
| `select_template` | 大纲确认后 | 简短确认 | 保存 style_spec.json，更新 session.json |
| `list_templates` | 用户主动要求 | 模板列表 | 无 |
| `generate_slides` | 模板确认后 | 文件路径列表 + 失败警告 | 并发 LLM 调用，保存 HTML，更新 session.json |
| `export_pptx` | 幻灯片生成后 | PPTX 路径 + 失败警告 | 并发截图，更新 session.json |

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
```

---

## 4. 会话状态机

### 4.1 PipelineStep 枚举

```
IDLE → OUTLINE_DONE → TEMPLATE_DONE → SLIDES_DONE → EXPORTED
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
class KeyPoint(BaseModel):
    text: str                                    # 完整陈述（必填）
    sub_points: list[str] = []                   # 可选子要点
    emphasis: Literal["high", "medium", "low"] = "medium"

class SlideItem(BaseModel):
    page: int = Field(ge=1)
    layout: Literal["cover", "toc", "content", "section", "ending"]
    title: str
    key_points: list[KeyPoint] = Field(default_factory=list)

class Outline(BaseModel):
    title: str
    slides: list[SlideItem]  # 不能为空
```

`KeyPoint` 支持**灵活层级**：简单内容保持扁平（只有 text），复杂内容用 `sub_points` 展开说明。`emphasis` 标记重点，影响幻灯片视觉呈现。向后兼容旧的字符串列表格式（自动转为 `KeyPoint(text=item)`）。

重试时将 `ValidationError` 的具体错误信息反馈给 LLM，提高修复率。

---

## 5. HTML 幻灯片规范

### 5.1 画布规格

```
尺寸：1280 × 720 px（16:9）
字体：'Microsoft YaHei', 'PingFang SC', sans-serif
渲染：Playwright Chromium，viewport 1280×720，device_scale_factor=2
```

### 5.2 Style Spec 结构

每个模板包含 `style_spec.json`，定义配色、字体、间距、组件样式、**三级强调样式**。

```json
{
  "emphasis": {
    "high": { "font_size": "24px", "color": "#ed8936", "font_weight": "bold" },
    "medium": { "font_size": "20px", "color": "#2d3748", "font_weight": "normal" },
    "low": { "font_size": "16px", "color": "#a0aec0", "font_weight": "normal" }
  },
  "component_styles": { ... }
}
```

### 5.3 布局类型

`cover` / `toc` / `content` / `section` / `ending`

---

## 6. 导出管线

```
HTML → Playwright 截图(2x, 并发) → PNG → python-pptx 嵌入 → .pptx
```

- 浏览器实例复用：一次启动，所有页面在同一浏览器中截图
- 并发控制：`Semaphore(5)` 限制同时打开的 page 数量
- 截图分辨率：2560×1440（2x 缩放）

---

## 7. 项目结构

```
ppt-agent/
├── pyproject.toml
├── .env.example
│
├── src/ppt_agent/
│   ├── main.py                 # CLI 入口（会话隔离 + contextvar）
│   ├── config.py               # Pydantic Settings + 并发配置 + 会话目录 contextvar
│   ├── llm.py                  # get_model() 工厂函数
│   │
│   ├── agent/
│   │   ├── agent.py            # create_deep_agent 定义
│   │   ├── prompts.py          # 主 Agent 系统提示词
│   │   ├── subagents.py        # （保留备用）
│   │   └── state.py            # KeyPoint + Outline + SessionState + SessionIndex + PipelineStep
│   │
│   ├── tools/
│   │   ├── outline.py          # generate_outline（Pydantic 校验 + 重试 + materials）
│   │   ├── template.py         # select_template / list_templates
│   │   ├── slide_gen.py        # generate_slides（并发 LLM 调用 + 容错）
│   │   ├── export.py           # export_pptx（并发截图 + 容错）
│   │   └── upload.py           # upload_and_parse（markitdown 文档解析）
│   │
│   ├── templates/
│   │   ├── registry.py
│   │   ├── simple_business/
│   │   ├── tech_dark/
│   │   ├── education/
│   │   ├── creative/
│   │   └── report/
│   │
│   ├── export/
│   │   ├── renderer.py         # Playwright（浏览器复用 + 单页截图）
│   │   └── pptx_builder.py     # python-pptx 组装
│   │
│   ├── prompts/
│   │   ├── outline.py
│   │   ├── slide.py
│   │   └── style.py
│   │
│   └── api/
│       ├── app.py               # FastAPI 应用 + CORS + 中间件
│       ├── server.py            # uvicorn 启动入口
│       ├── deps.py              # 依赖注入（agent 单例）
│       ├── streaming.py         # SSE 流式生成器
│       └── routes/
│           ├── sessions.py      # 会话 CRUD + 消息 + 上传 + 下载
│           ├── templates.py     # 模板查询
│           └── upload.py        # 文件上传处理
│
└── tests/
    ├── test_tools.py           # 23 个测试（模板、工具、校验、状态、会话索引、上传）
    └── test_renderer.py        # 渲染和 PPTX 管线测试
```

---

## 8. MVP 状态

### 8.1 已完成

- [x] CLI 对话入口（单 event loop，async）
- [x] 6 阶段完整流程（含文件上传）
- [x] 6 个 async Tools
- [x] 并发幻灯片生成（Semaphore 控制并发数 + return_exceptions 容错）
- [x] 并发 PNG 渲染（浏览器复用 + Semaphore + 容错）
- [x] 5 个预设模板
- [x] Playwright 2x 截图 + python-pptx 导出
- [x] 4 个 LLM 提供商
- [x] Outline Pydantic 校验 + 结构化重试
- [x] KeyPoint 层级模型（text + sub_points + emphasis）
- [x] 页数自适应（LLM 根据内容复杂度决定页数，或用户指定）
- [x] SessionState 状态机（损坏文件自动回退）
- [x] 会话隔离（每次生成独立目录，contextvars 传递会话上下文）
- [x] SessionIndex 会话索引（index.json，前端可读取列表）
- [x] 三级强调样式（模板 emphasis 定义）
- [x] 文件上传与解析（markitdown：docx/xlsx/pdf/html/图片等，20MB 限制）
- [x] 参考材料融入大纲（materials.md 自动读取 + materials 参数传递）
- [x] 容错机制（单页生成失败不影响整体、HTML 有效性校验、PPTX 嵌入异常跳过、GraphInterrupt 恢复）
- [x] 23 个单元测试
- [x] Debug 输出（TOOL 调用/结果追踪）

### 8.2 API 服务器

- [x] FastAPI 应用（CORS + 中间件）
- [x] SSE 流式对话
- [x] 会话管理（CRUD）
- [x] 文件上传（multipart）
- [x] PPTX 下载
- [x] 模板查询
- [x] 会话上下文中间件（从 URL 提取 session_id）

### 8.3 前端界面

- [x] Vue 3 + TypeScript 项目结构
- [x] Pinia 状态管理（sessions store + session store）
- [x] SSE 实时流式展示
- [x] Markdown 渲染（marked）
- [x] 文件上传（drag & drop）
- [x] 会话管理（创建、列表、删除、切换）
- [x] 响应式设计

### 8.4 待开发

- [ ] 联网搜索/研究
- [ ] AI 自定义风格生成
- [ ] PDF 导出
- [ ] 更多提供商

---

## 9. 关键设计决策记录

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

### 9.11 KeyPoint 灵活层级模型

**选择**：`KeyPoint` 包含 `text`（必填）、`sub_points`（可选）、`emphasis`（可选），而非固定深度结构。
**原因**：不同 PPT 的内容复杂度差异大。简单页面保持扁平，复杂页面用 `sub_points` 展开。强调级别（high/medium/low）控制视觉层次，让幻灯片有重点而非平铺罗列。向后兼容旧的字符串列表格式。

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
