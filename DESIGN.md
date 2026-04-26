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
| **需求讨论** | 主 Agent 对话 | 用户消息 | 确认的主题/页数/风格 | 0 次（纯对话） |
| **大纲生成** | `generate_outline` tool | 主题、页数 | outline.json（Pydantic 校验） | 1 次（含重试） |
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

### 2.3 前端（未来）

| 组件 | 选型 |
|------|------|
| 框架 | Vue 3 + TypeScript |
| 构建 | Vite |
| 状态管理 | Pinia |

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
    ],
    checkpointer=MemorySaver(),
    backend=FilesystemBackend(root_dir="output"),
)
```

所有 tool 均为 `async`，在单一 event loop 中运行。

### 3.2 主 Agent Tools

| Tool | 触发时机 | 输出 | 副作用 |
|------|----------|------|--------|
| `generate_outline` | 主题确认后 | 大纲 JSON | 保存 outline.json，更新 session.json |
| `select_template` | 大纲确认后 | 简短确认 | 保存 style_spec.json，更新 session.json |
| `list_templates` | 用户主动要求 | 模板列表 | 无 |
| `generate_slides` | 模板确认后 | 文件路径列表 | 并发 LLM 调用，保存 HTML，更新 session.json |
| `export_pptx` | 幻灯片生成后 | PPTX 路径 | 并发截图，更新 session.json |

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
    step: PipelineStep
    title: str
    outline_file: str
    style_spec_file: str
    slides_dir: str
    pptx_file: str
    template_key: str
```

每次 tool 执行后更新 `session.json`，确保各 tool 间的数据流转有据可查，不依赖隐式文件命名约定。

### 4.3 大纲校验

```python
class SlideItem(BaseModel):
    page: int = Field(ge=1)
    layout: Literal["cover", "toc", "content", "section", "ending"]
    title: str
    key_points: list[str] = Field(default_factory=list)

class Outline(BaseModel):
    title: str
    slides: list[SlideItem]  # 不能为空
```

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

每个模板包含 `style_spec.json`，定义配色、字体、间距、组件样式。

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
│   ├── main.py                 # CLI 入口（async, 单 event loop）
│   ├── config.py               # Pydantic Settings + 并发配置
│   ├── llm.py                  # get_model() 工厂函数
│   │
│   ├── agent/
│   │   ├── agent.py            # create_deep_agent 定义
│   │   ├── prompts.py          # 主 Agent 系统提示词
│   │   ├── subagents.py        # （保留备用）
│   │   └── state.py            # Outline + SessionState + PipelineStep
│   │
│   ├── tools/
│   │   ├── outline.py          # generate_outline（Pydantic 校验 + 重试）
│   │   ├── template.py         # select_template / list_templates
│   │   ├── slide_gen.py        # generate_slides（并发 LLM 调用）
│   │   └── export.py           # export_pptx（并发截图）
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
│
└── tests/
    ├── test_tools.py           # 17 个测试（模板、工具、校验、状态）
    └── test_renderer.py        # 渲染和 PPTX 管线测试
```

---

## 8. MVP 状态

### 8.1 已完成

- [x] CLI 对话入口（单 event loop，async）
- [x] 5 阶段完整流程
- [x] 5 个 async Tools
- [x] 并发幻灯片生成（Semaphore 控制并发数）
- [x] 并发 PNG 渲染（浏览器复用 + Semaphore）
- [x] 5 个预设模板
- [x] Playwright 2x 截图 + python-pptx 导出
- [x] 4 个 LLM 提供商
- [x] Outline Pydantic 校验 + 结构化重试
- [x] SessionState 状态机
- [x] 17 个单元测试
- [x] Debug 输出（TOOL 调用/结果追踪）

### 8.2 待开发

- [ ] 前端界面
- [ ] 文件上传与解析（markitdown）
- [ ] 联网搜索/研究
- [ ] AI 自定义风格生成
- [ ] PDF 导出
- [ ] 流式输出
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
