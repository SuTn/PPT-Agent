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

```bash
uv run ppt-agent
```

## 工作流程

```
对话确认主题 → 生成大纲 → 选择模板 → 并发生成幻灯片 → 导出 PPTX
```

每步完成后会展示结果，用户确认或提出修改后再继续。

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

## 并发配置

| 环境变量 | 默认值 | 说明 |
|--------|--------|------|
| `PPT_AGENT_SLIDE_CONCURRENCY` | 3 | 幻灯片 LLM 并发数 |
| `PPT_AGENT_RENDER_CONCURRENCY` | 5 | Playwright 截图并发数 |

## 测试

```bash
uv run pytest tests/ -v
```

## 架构

- **主 Agent**：调度 5 个 async tool，管理对话流程
- **并发生成**：`asyncio.gather()` + `Semaphore` 控制幻灯片生成和渲染并发
- **状态机**：`SessionState` 跟踪流程进度，Pydantic 校验大纲结构
- **导出管线**：HTML → Playwright 截图(2x) → python-pptx 嵌入

详见 [DESIGN.md](DESIGN.md)。
