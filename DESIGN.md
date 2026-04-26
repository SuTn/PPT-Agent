# PPT-Agent 设计方案

> 通过对话与可选文件上传，AI 驱动的 PowerPoint 演示文稿生成系统。
> 核心路径：LLM 生成 HTML 幻灯片 → 截图嵌入 PPTX（无图像生成模型依赖）。

---

## 1. 架构概览

### 1.1 核心流程

```
用户对话 → [需求讨论] → [大纲生成] → [风格选择] → [幻灯片生成] → [导出 PPTX]
               tool           tool          tool        子代理(task)        tool
```

用户可随时对话、修改、补充，整个流程是**状态机**而非线性管道。

### 1.2 各阶段职责

| 阶段 | 实现方式 | 输入 | 输出 | LLM 调用 |
|------|----------|------|------|----------|
| **需求讨论** | 主 Agent 对话 | 用户消息 | 确认的主题/页数/风格 | 0 次（纯对话） |
| **大纲生成** | `generate_outline` tool | 主题、页数 | 大纲 JSON → outline.json | 1 次（含重试） |
| **风格选择** | `select_template` tool | 模板名 | style_spec.json | 0 次 |
| **幻灯片生成** | `slide_generator` 子代理 | outline + style_spec | N 个 HTML 文件 | N 次（子代理上下文） |
| **导出** | `export_pptx` tool | slides/ 目录 | .pptx 文件 | 0 次 |

### 1.3 上下文优化

幻灯片生成通过**子代理隔离**，主 Agent 只看到 task 调用和文件路径结果，N 页 HTML 内容不会进入主对话上下文。

---

## 2. 技术栈

### 2.1 后端

| 组件 | 选型 | 说明 |
|------|------|------|
| **Agent 框架** | LangChain Deep Agents | `create_deep_agent`，内置文件系统、子代理、工具调用 |
| **Web 框架** | FastAPI | 异步，未来扩展 API 服务 |
| **HTML 渲染** | Playwright | 无头浏览器，截图 HTML → PNG（2x 分辨率） |
| **PPTX 生成** | python-pptx | 纯 Python，截图作为幻灯片背景嵌入 |
| **配置管理** | Pydantic Settings | 环境变量 + .env 文件 |
| **包管理** | uv | 快速依赖管理与虚拟环境 |

### 2.2 LLM 提供商

通过统一 `get_model()` 工厂函数创建实例，均通过 OpenAI 兼容接口对接：

| 提供商 | model 格式 | 依赖 | 状态 |
|--------|-----------|------|------|
| Anthropic | `anthropic:claude-sonnet-4-6` | `langchain-anthropic` | 已实现 |
| OpenAI | `openai:gpt-4o` | `langchain-openai` | 已实现 |
| 智谱 | `zhipu:glm-4` / `zhipu:glm-5-turbo` | `langchain-openai` + OpenAI 兼容接口 | 已实现 |
| VLLM | `vllm:Qwen/Qwen2.5-72B` | `langchain-openai` + 自定义 base_url | 已实现 |

智谱和 VLLM 均通过 `ChatOpenAI(base_url=..., api_key=...)` 对接。

### 2.3 前端（未来）

| 组件 | 选型 |
|------|------|
| 框架 | Vue 3 + TypeScript |
| 构建 | Vite |
| UI 库 | 待定 |
| 状态管理 | Pinia |

---

## 3. Deep Agents 架构

### 3.1 Agent 定义

```python
agent = create_deep_agent(
    model=get_model(),                    # 通过工厂函数创建，支持所有提供商
    system_prompt=SYSTEM_PROMPT,
    tools=[generate_outline, select_template, list_templates, export_pptx],
    subagents=[slide_generator],          # 幻灯片生成拆为独立子代理
    checkpointer=MemorySaver(),           # 会话状态持久化
    backend=FilesystemBackend(root_dir="output"),
)
```

### 3.2 主 Agent Tools

| Tool | 触发时机 | 输入 | 输出 |
|------|----------|------|------|
| `generate_outline` | 主题确认后 | requirements, page_count | 大纲 JSON（保存到 outline.json） |
| `select_template` | 大纲确认后 | template_key | 简短确认 + 保存 style_spec.json |
| `list_templates` | 用户主动要求 | 无 | 模板列表 |
| `export_pptx` | 幻灯片生成后 | slides_dir | PPTX 文件路径 |

### 3.3 子代理：slide_generator

幻灯片生成拆为独立子代理，通过 `task` 工具由主 Agent 调用：

- **读取文件**：`read_file("outline.json")` + `read_file("style_spec.json")`
- **逐页生成**：按大纲顺序为每页生成完整 HTML
- **写入文件**：`write_file("slides/slide_XX_layout.html", html_content)`
- **返回结果**：已生成的文件路径列表

**上下文隔离**：N 页 HTML 的生成过程和内容全部在子代理上下文中，不进入主 Agent。

### 3.4 提供商配置

```python
class Settings(BaseSettings):
    model_config = {"env_prefix": "PPT_AGENT_", "env_file": ".env", "extra": "ignore"}

    model: str = "anthropic:claude-sonnet-4-6"
    output_dir: Path = Path("./output")
    vllm_base_url: str = ""
    vllm_api_key: str = "empty"
    zhipu_base_url: str = "https://open.bigmodel.cn/api/paas/v4"
    zhipu_api_key: str = ""
```

---

## 4. HTML 幻灯片规范

### 4.1 画布规格

```
尺寸：1280 × 720 px（16:9）
字体：'Microsoft YaHei', 'PingFang SC', sans-serif
渲染：Playwright Chromium，viewport 1280×720，device_scale_factor=2
```

### 4.2 单页 HTML 结构

每张幻灯片是一个**完整的、自包含的 HTML 文件**，固定画布，body overflow: hidden。

### 4.3 Style Spec 结构

每个模板包含 `style_spec.json`，定义：

| 字段 | 说明 |
|------|------|
| `colors` | 配色方案（primary, secondary, accent, background, text 等） |
| `typography` | 字体和字号（title_size, body_size, line_height 等） |
| `layout` | 间距和布局参数 |
| `component_styles` | 各布局类型的具体样式描述 |

### 4.4 布局类型

| 类型 | 用途 |
|------|------|
| `cover` | 封面页，大标题居中 |
| `toc` | 目录页，章节列表 |
| `content` | 内容页，标题 + 要点 |
| `section` | 章节分隔页 |
| `ending` | 结束页 |

---

## 5. 导出管线

```
HTML 文件 → Playwright 截图(2x) → PNG → python-pptx 嵌入为整页背景 → .pptx
```

- 截图分辨率：2560×1440（2x 缩放），保证清晰度
- PPTX 尺寸：13.333" × 7.5"（标准 16:9）
- 每页 PNG 作为全幅背景图嵌入空白幻灯片

---

## 6. 项目结构

```
ppt-agent/
├── pyproject.toml                  # 项目配置（uv）
├── CLAUDE.md                       # 开发规范
├── DESIGN.md                       # 本文档
├── README.md                       # 使用说明
├── .env.example                    # 环境变量模板
│
├── src/ppt_agent/
│   ├── main.py                     # CLI 入口
│   ├── config.py                   # Pydantic Settings 配置
│   ├── llm.py                      # get_model() 工厂函数
│   │
│   ├── agent/
│   │   ├── agent.py                # create_deep_agent 定义
│   │   ├── prompts.py              # 主 Agent 系统提示词
│   │   ├── subagents.py            # slide_generator 子代理定义
│   │   └── state.py                # 状态常量
│   │
│   ├── tools/
│   │   ├── outline.py              # generate_outline（含 JSON 容错+重试）
│   │   ├── template.py             # select_template / list_templates
│   │   ├── slide_gen.py            # generate_slides（备用，当前由子代理替代）
│   │   └── export.py               # export_pptx
│   │
│   ├── templates/
│   │   ├── registry.py             # 模板注册表
│   │   ├── simple_business/        # 简约商务
│   │   ├── tech_dark/              # 科技深色
│   │   ├── education/              # 教育培训
│   │   ├── creative/               # 创意设计
│   │   └── report/                 # 数据报告
│   │
│   ├── export/
│   │   ├── renderer.py             # Playwright HTML → PNG
│   │   └── pptx_builder.py         # PNG → PPTX 组装
│   │
│   ├── prompts/
│   │   ├── outline.py              # 大纲生成提示词
│   │   ├── slide.py                # 幻灯片 HTML 提示词
│   │   └── style.py                # 风格提示词
│   │
│   └── api/                        # 未来 FastAPI 接口
│
├── tests/
│   ├── test_tools.py               # 工具和模板测试
│   └── test_renderer.py            # 渲染和 PPTX 管线测试
│
└── output/                         # 运行时生成（.gitignore）
    ├── outline.json
    ├── style_spec.json
    ├── slides/                     # HTML 幻灯片
    └── pptx/                       # 导出的 PPTX
```

---

## 7. MVP 状态

### 7.1 已完成

- [x] CLI 对话入口
- [x] 5 阶段完整流程
- [x] 4 个主 Agent Tools（outline, template, export）
- [x] slide_generator 子代理（上下文隔离）
- [x] 5 个预设模板
- [x] Playwright 2x 截图 + python-pptx 导出
- [x] 4 个 LLM 提供商（Anthropic, OpenAI, 智谱, VLLM）
- [x] JSON 容错解析 + 3 次重试
- [x] 9 个单元测试
- [x] Debug 输出（TOOL 调用/结果追踪）

### 7.2 待开发

- [ ] 前端界面
- [ ] 文件上传与解析（markitdown）
- [ ] 联网搜索/研究
- [ ] AI 自定义风格生成
- [ ] PDF 导出
- [ ] 流式输出
- [ ] 更多提供商（MiniMax 等）

---

## 8. 开发计划

### Phase 1-4: MVP（已完成）

1. 项目初始化、配置管理
2. Deep Agent + Tools + 子代理
3. 5 个模板 + 提示词
4. 联调测试

### Phase 5: 增强（下一步）

- [ ] 文件解析（markitdown 支持 PDF/Word/Excel）
- [ ] 联网搜索（搜索 API 集成）
- [ ] AI 自定义风格（用户描述 → style_spec）
- [ ] 流式输出（展示生成进度）

### Phase 6: 产品化

- [ ] FastAPI REST API
- [ ] Vue 前端
- [ ] PDF 导出
- [ ] 更多模板与提供商

---

## 9. 关键设计决策记录

### 9.1 子代理隔离幻灯片生成

**选择**：幻灯片生成拆为 `slide_generator` 子代理，不作为主 Agent tool。
**原因**：N 页 HTML 内容若全部进入主 Agent 上下文会快速撑爆。子代理上下文临时、用完释放，主 Agent 只接收文件路径摘要。

### 9.2 HTML 而非 SVG/Canvas

**选择**：每张幻灯片生成完整 HTML 文件。
**原因**：HTML 生态最成熟，CSS 布局灵活，字体支持好，Playwright 渲染稳定。

### 9.3 截图嵌入而非原生 PPTX 对象

**选择**：HTML → PNG 截图 → 作为背景嵌入 PPTX。
**原因**：python-pptx 原生形状能力有限，无法还原复杂 CSS 布局。截图保证像素级还原。

### 9.4 Style Spec 嵌入模板而非 AI 生成

**选择**：MVP 阶段 style_spec 由模板预设。
**原因**：零 LLM 调用，结果确定可控。避免"生成 HTML → 提取风格"的循环依赖。

### 9.5 OpenAI 兼容接口统一多提供商

**选择**：智谱和 VLLM 均通过 `ChatOpenAI(base_url=...)` 对接。
**原因**：智谱提供 OpenAI 兼容端点，VLLM 原生兼容。一套 SDK 覆盖所有提供商，减少维护成本。

### 9.6 无 interrupt_on

**选择**：MVP 不使用 `interrupt_on` 暂停机制。
**原因**：CLI 场景下用户主动发起操作，暂停反而打断流程。通过系统提示词控制确认节奏更自然。
