# PPT-Agent

通过对话生成 PowerPoint 演示文稿的 AI Agent。LLM 生成 HTML 幻灯片，Playwright 截图后嵌入 PPTX。

## 快速开始

### 1. 安装依赖

```bash
uv sync
uv run playwright install chromium
```

### 2. 配置 API Key

```bash
cp .env.example .env
```

编辑 `.env`，至少配置一个提供商：

```env
# Anthropic
ANTHROPIC_API_KEY=sk-ant-xxx
PPT_AGENT_MODEL=anthropic:claude-sonnet-4-6

# 或 OpenAI
OPENAI_API_KEY=sk-xxx
PPT_AGENT_MODEL=openai:gpt-4o

# 或智谱
PPT_AGENT_ZHIPU_API_KEY=your-key
PPT_AGENT_MODEL=zhipu:glm-4

# 或 VLLM（自部署）
PPT_AGENT_VLLM_BASE_URL=http://localhost:8000/v1
PPT_AGENT_MODEL=vllm:Qwen/Qwen2.5-72B-Instruct
```

### 3. 运行

**CLI 模式**:
```bash
uv run ppt-agent
```

**API 服务器**:
```bash
uv run ppt-agent-api
```

然后访问 http://localhost:9999 或启动前端：

```bash
cd web
npm install
npm run dev
```

前端开发服务器默认运行在 http://localhost:5173。

## 工作流程

```
对话确认主题 → [可选] 上传文件 → 生成大纲 → 选择模板 → 并发生成幻灯片 → 导出 PPTX
```

每步完成后会展示结果，用户确认或提出修改后再继续。页数默认由 LLM 根据内容复杂度自适应决定。

## CLI 命令

| 命令 | 说明 |
|------|------|
| `/new` | 新建会话（之前的 PPT 保留在 output/ 中） |
| `/upload` | 上传文件（docx/xlsx/pdf/图片等，解析为 Markdown 融入大纲） |
| `/quit` | 退出 |

## 支持的 LLM 提供商

| 提供商 | model 格式 |
|--------|-----------|
| Anthropic | `anthropic:claude-sonnet-4-6` |
| OpenAI | `openai:gpt-4o` |
| 智谱 | `zhipu:glm-4` |
| VLLM | `vllm:model-name` |

## 预设模板

- `simple_business` — 简约商务（蓝白配色）
- `tech_dark` — 科技深色（深蓝黑 + 霓虹色）
- `education` — 教育培训（清新绿色）
- `creative` — 创意设计（渐变 + 不对称布局）
- `report` — 数据报告（灰白 + 图表元素）

每个模板均定义了三级强调样式（high/medium/low），用于视觉层次控制。

## 并发配置

| 环境变量 | 默认值 | 说明 |
|--------|--------|------|
| `PPT_AGENT_SLIDE_CONCURRENCY` | 3 | 幻灯片 LLM 并发数 |
| `PPT_AGENT_RENDER_CONCURRENCY` | 5 | Playwright 截图并发数 |

## 测试

```bash
uv run pytest tests/ -v
```

## API 接口

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/v1/sessions` | POST | 创建新会话 |
| `/api/v1/sessions` | GET | 列出所有会话 |
| `/api/v1/sessions/{id}` | GET | 获取会话详情（含历史消息） |
| `/api/v1/sessions/{id}` | DELETE | 删除会话 |
| `/api/v1/sessions/{id}/messages` | POST | 发送消息（非流式） |
| `/api/v1/sessions/{id}/stream` | GET | SSE 流式对话 |
| `/api/v1/sessions/{id}/upload` | POST | 上传文件 |
| `/api/v1/sessions/{id}/download` | GET | 下载 PPTX |
| `/api/v1/templates` | GET | 获取模板列表 |

## 架构

- **主 Agent**：调度 6 个 async tool，管理对话流程，主动收集受众/核心信息
- **API 层**：FastAPI 实现 SSE 流式对话、会话管理、文件上传、模板查询
- **前端**：Vue 3 + TypeScript + Vite + Pinia，实时流式展示对话和工具进度
- **文档解析**：`upload_and_parse` 通过 markitdown 解析上传文件（docx/xlsx/pdf/图片等），保存为 materials.md 融入大纲生成
- **内容质量**：`KeyPoint` 模型支持灵活层级（text + sub_points + emphasis），大纲根据内容复杂度智能决定结构和页数
- **会话隔离**：每次 PPT 生成独立目录，`contextvars` + 中间件传递会话上下文，`SessionIndex` 管理历史
- **对话持久化**：SQLite 持久化 agent 对话历史，重启后前端可恢复历史会话
- **容错机制**：`asyncio.gather(return_exceptions=True)` 单页失败不影响整体；HTML 有效性校验；PPTX 嵌入异常跳过
- **并发生成**：`asyncio.gather()` + `Semaphore` 控制幻灯片生成和渲染并发
- **状态机**：`SessionState` 跟踪流程进度，Pydantic 校验大纲结构
- **导出管线**：HTML → Playwright 截图(2x) → python-pptx 嵌入

## 输出目录结构

```
output/
├── index.json              # 会话索引（所有 PPT 生成记录）
├── checkpoints.db          # SQLite 对话历史持久化
├── a1b2c3d4/               # 单个会话目录
│   ├── session.json        # 会话状态（PipelineStep）
│   ├── outline.json        # 大纲（KeyPoint 结构）
│   ├── style_spec.json     # 模板风格规范
│   ├── materials.md        # 上传材料（Markdown 格式，可选）
│   ├── slides/             # HTML 幻灯片
│   │   ├── slide_01_cover.html
│   │   └── ...
│   └── {标题}.pptx         # 最终 PPTX
└── e5f6g7h8/
    └── ...
```

详见 [DESIGN.md](DESIGN.md)。
