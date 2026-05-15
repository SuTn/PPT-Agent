# Session 状态同步问题记录
帮我分析一个问题，先不要修改代码，我在前端创建一个PPT生成任务，当我刷新那个session页面之后，加入在申城PPT野蛮阶  
  段，他就不会显示生成了几页，只会显示正在生成幻灯片，不刷新之前还能看到生成了一半，每一页的详情，关于每个session  
  的进度，有的被中断了，前端还是现在正在进行xx任务，实际没有在跑，这里问题比较多

> 创建时间：2026/05/15
> 状态：待优化
> 优先级：高

## 问题概述

前端 session 页面刷新后，无法恢复 PPT 生成进度；任务中断后前端仍显示"进行中"。

---

## 问题 1：刷新后丢失"生成了一半"的进度

### 现象
- 生成 PPT 进行到一半（假设 5/10 页）时刷新页面
- 前端不显示已生成的 5 页详情，只显示"正在生成幻灯片"
- 不刷新之前能看到完整的生成进度

### 根因
**前端 `loadHistory` 只在 `step === "slides_done"` 或 `step === "exported"` 时才加载 slides 信息**

**代码位置**：`web/src/stores/session.ts` 第 70-76 行

```typescript
// Restore slides from API if slides are done
const slideSteps = ["slides_done", "exported"];
if (slideSteps.includes(pipelineStep.value)) {
  try {
    const { data: sd } = await client.get(`/sessions/${sessionId}/slides`);
    if (sd?.slides) slides.value = sd.slides;
  } catch { /* no slides */ }
}
```

**问题链条**：

1. `generate_slides` 工具只在**所有幻灯片生成完成后**才更新 `session.json` 中的 `step` 为 `SLIDES_DONE`（`src/ppt_agent/tools/slide_gen.py` 第 324-328 行）
2. 生成过程中 step 仍是中间状态（如 `template_done`）
3. 前端刷新后读取到的是中间 step，不满足 `slideSteps` 条件
4. `/sessions/{id}/slides` API 从未被调用，已生成的 HTML 文件信息丢失

**注意**：HTML 文件在生成时已立即写入磁盘（`slide_gen.py` 第 310 行），但前端无法发现。

---

## 问题 2：任务中断后前端仍显示"正在进行"

### 现象
- session 显示"正在生成幻灯片"，但实际没有在跑
- 无刷新页面也无法恢复

### 根因
**进度队列是纯内存存储，SSE 断开后无状态同步机制**

**代码位置**：`src/ppt_agent/progress.py` 第 5-11 行

```python
_queues: dict[str, asyncio.Queue] = {}  # 内存存储，进程重启丢失
```

**问题链条**：

1. `generate_slides` 通过 `queue.put()` 发送 `slide_generated` 事件存储在内存队列
2. SSE 连接断开（刷新/网络中断/浏览器崩溃）时：
   - 内存队列剩余事件丢失
   - 服务器端任务可能还在运行
   - `remove_queue(session_id)` 在 `finally` 块执行
3. 前端刷新后：
   - `isStreaming` 重置为 `false`
   - `pipelineStep` 读取 `session.json` 中仍是中间状态
   - **无轮询机制检测服务器端真实任务状态**
   - 前端无法区分"任务中断"和"任务还在中间阶段"

---

## 问题 3：step 更新时机问题

### 现象
- 前端 pipelineStep 状态依赖 `tool_result` 事件更新
- `slide_generated` 事件只更新 `slides` 数组，不更新 step

### 代码位置
`web/src/stores/session.ts` 第 149-151 行

```typescript
// Only tool_result events update pipelineStep
if (event.type === "tool_result") {
  pipelineStep.value = inferStep(toolName);
}
```

---

## 问题链条图

```
生成进行中 (step = template_done)
    ↓
前端刷新 → loadHistory() → step 还是 template_done
    ↓
slideSteps 条件不满足 → 跳过加载 /slides API
    ↓
slides.value = [] → 前端显示"正在生成"但没有进度详情
```

---

## 关键代码位置

| 问题 | 文件 | 行号 |
|------|------|------|
| slideSteps 条件过严 | `web/src/stores/session.ts` | 70-76 |
| 纯内存队列无持久化 | `src/ppt_agent/progress.py` | 5-11 |
| step 只在 tool_result 更新 | `web/src/stores/session.ts` | 149-151 |
| SSE 断开后无状态同步 | `src/ppt_agent/api/streaming.py` | 38-52 |
| step 只在生成完成后更新 | `src/ppt_agent/tools/slide_gen.py` | 324-328 |
| slides 目录扫描 API | `src/ppt_agent/api/routes/sessions.py` | 169-190 |

---

## 核心设计缺陷

1. **进度信息只通过 SSE 实时推送，不持久化**
   - 已生成的幻灯片文件在磁盘上，但前端无法发现
   - 需要前端在加载历史时主动扫描 slides 目录

2. **前端无轮询机制**
   - SSE 断开后无法检测服务器任务真实状态
   - 需要轮询 `/sessions/{id}` 或新增专门的健康检查端点

3. **loadHistory 的 slideSteps 条件过于严格**
   - 应该是"只要有 slides 目录存在就尝试加载"
   - 而非"只有 slides_done 才加载"

---

## 待优化项

### 高优先级
- [ ] 修复 `loadHistory` 的 slideSteps 条件，改为"只要 slides 目录存在就加载"
- [ ] 前端添加轮询机制，检测 session 真实状态
- [ ] 服务器端记录每个 slide 的生成状态到 session.json

### 中优先级
- [ ] 考虑将进度信息持久化到 session.json
- [ ] 新增健康检查端点，返回当前任务真实状态

### 低优先级
- [ ] 前端显示"任务可能已中断"的提示
- [ ] 支持恢复中断的任务

---

## 修复方向建议

### 方案 A：前端主动扫描（简单）
- 修改 `loadHistory` 逻辑，只要 session.json 中存在 `slides_dir` 就调用 `/slides` API
- 前端定时轮询 `/sessions/{id}` 检查状态变化

### 方案 B：进度持久化（彻底）
- 每生成一张幻灯片就更新 `session.json` 中的进度
- 前端刷新后读取 `session.json` 即可恢复完整进度
- 需要修改 `slide_gen.py` 的更新策略

### 方案 C：混合方案（推荐）
- 方案 B 的持久化 + 方案 A 的轮询
- 最可靠但改动较大