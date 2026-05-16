<template>
  <div class="message-list" ref="listRef">
    <div v-if="messages.length === 0" class="empty-hero">
      <div class="hero-icon">P</div>
      <h3>创建你的演示文稿</h3>
      <p>描述你想要的 PPT 主题，AI 将帮你完成设计</p>
      <div class="hero-chips">
        <button v-for="chip in suggestions" :key="chip" class="chip" @click="$emit('send', chip)">
          {{ chip }}
        </button>
      </div>
    </div>
    <div
      v-for="(msg, i) in messages"
      :key="i"
      :class="['message', `message--${msg.role}`]"
    >
      <template v-if="msg.role === 'user'">
        <div class="message-bubble message-bubble--user">{{ msg.content }}</div>
      </template>
      <template v-else-if="msg.role === 'assistant'">
        <div v-if="msg.toolCalls" class="tool-card" :class="{ completed: isToolCompleted(i) }">
          <div class="tool-card-icon" :class="{ spinning: !isToolCompleted(i) }">
            <svg v-if="isToolCompleted(i)" width="16" height="16" viewBox="0 0 16 16" fill="none">
              <path d="M2 8l4 4 8-8" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
            <svg v-else width="16" height="16" viewBox="0 0 16 16" fill="none">
              <path d="M8 1v2M8 13v2M1 8h2M13 8h2M3.05 3.05l1.41 1.41M11.54 11.54l1.41 1.41M3.05 12.95l1.41-1.41M11.54 4.46l1.41-1.41" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
            </svg>
          </div>
          <span class="tool-card-text">{{ isToolCompleted(i) ? completedLabel(msg.toolCalls[0].name) : toolLabel(msg.toolCalls[0].name) }}</span>
        </div>
        <div v-else class="assistant-row">
          <div class="avatar">AI</div>
          <div class="message-bubble message-bubble--assistant" v-html="renderMarkdown(msg.content)"></div>
        </div>
      </template>
      <template v-else>
        <OutlinePreview v-if="isOutlineResult(msg) && props.outline" :outline="props.outline" />
        <ResearchPreview v-else-if="isResearchResult(msg) && props.researchNotes" :content="props.researchNotes" />
        <div v-else class="system-notice">
          <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
            <circle cx="7" cy="7" r="6" stroke="currentColor" stroke-width="1.2"/>
            <path d="M7 4v4M7 10v0.5" stroke="currentColor" stroke-width="1.2" stroke-linecap="round"/>
          </svg>
          <span>{{ msg.content }}</span>
        </div>
      </template>
    </div>
    <div v-if="isStreaming" class="streaming-bar">
      <div class="streaming-pulse"></div>
      <span>AI 正在处理...</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, nextTick } from "vue";
import { marked } from "marked";
import DOMPurify from "dompurify";
import type { Message } from "../api/types";
import OutlinePreview from "./OutlinePreview.vue";
import ResearchPreview from "./ResearchPreview.vue";

const props = defineProps<{
  messages: Message[];
  isStreaming: boolean;
  researchNotes?: string;
  outline?: any;
}>();

defineEmits<{
  send: [content: string];
}>();

const suggestions = [
  "制作一份产品发布会的 PPT",
  "帮我做一份季度工作汇报",
  "设计一个技术架构分享演示",
];

const TOOL_LABELS: Record<string, string> = {
  research_topic: "正在研究主题...",
  generate_outline: "正在生成大纲...",
  select_template: "正在选择模板...",
  list_templates: "正在获取模板列表...",
  generate_slides: "正在生成幻灯片...",
  export_pptx: "正在导出 PPTX...",
  upload_and_parse: "正在解析上传文件...",
};

const COMPLETED_LABELS: Record<string, string> = {
  research_topic: "研究完成",
  generate_outline: "大纲已生成",
  select_template: "模板已选择",
  list_templates: "模板列表已获取",
  generate_slides: "幻灯片已生成",
  export_pptx: "PPTX 已导出",
  upload_and_parse: "文件已解析",
};

function toolLabel(name: string): string {
  return TOOL_LABELS[name] ?? `调用工具: ${name}`;
}

function completedLabel(name: string): string {
  return COMPLETED_LABELS[name] ?? `${name} 完成`;
}

function isToolCompleted(index: number): boolean {
  // A tool call is completed if the next message is a tool_result
  const next = props.messages[index + 1];
  return !!next && next.role === "system" && next.toolResult === true;
}

const listRef = ref<HTMLElement | null>(null);

function renderMarkdown(text: string): string {
  if (!text) return "";
  const raw = marked.parse(text, { async: false }) as string;
  return DOMPurify.sanitize(raw);
}

function scrollToBottom() {
  nextTick(() => {
    if (listRef.value) {
      listRef.value.scrollTop = listRef.value.scrollHeight;
    }
  });
}

function isOutlineResult(msg: Message): boolean {
  return msg.toolResult === true && msg.content.startsWith("[generate_outline]");
}

function isResearchResult(msg: Message): boolean {
  return msg.toolResult === true && msg.content.startsWith("[research_topic]");
}

watch([() => props.messages, () => props.isStreaming], () => {
  scrollToBottom();
}, { deep: true });
</script>

<style scoped>
.message-list {
  flex: 1;
  overflow-y: auto;
  padding: var(--space-xl);
  display: flex;
  flex-direction: column;
  gap: var(--space-lg);
}

/* Empty hero */
.empty-hero {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: var(--space-md);
  text-align: center;
  padding: var(--space-2xl);
}
.hero-icon {
  width: 56px;
  height: 56px;
  background: var(--primary);
  color: white;
  border-radius: var(--radius-lg);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  font-weight: 800;
  margin-bottom: var(--space-sm);
}
.empty-hero h3 {
  font-size: 18px;
  font-weight: 600;
  color: var(--text);
}
.empty-hero p {
  font-size: 14px;
  color: var(--muted);
}
.hero-chips {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-sm);
  margin-top: var(--space-md);
  justify-content: center;
}
.chip {
  padding: var(--space-sm) var(--space-lg);
  border: 1px solid var(--border);
  border-radius: 999px;
  background: var(--card);
  color: var(--text-secondary);
  font-size: 13px;
  cursor: pointer;
  transition: all var(--transition-fast);
}
.chip:hover {
  border-color: var(--primary-light);
  color: var(--primary);
  background: #eef2ff;
}

/* Messages */
.message {
  display: flex;
}
.message--user {
  justify-content: flex-end;
}
.message--assistant {
  justify-content: flex-start;
}
.message--system {
  justify-content: flex-start;
}

.message-bubble {
  max-width: 70%;
  padding: var(--space-md) var(--space-lg);
  border-radius: var(--radius-lg);
  line-height: 1.6;
  font-size: 14px;
  word-break: break-word;
}

.message-bubble--user {
  background: var(--primary);
  color: white;
  border-bottom-right-radius: var(--radius-sm);
  box-shadow: var(--shadow-sm);
}

.message-bubble--assistant {
  background: var(--card);
  border: 1px solid var(--border);
  border-bottom-left-radius: var(--radius-sm);
  box-shadow: var(--shadow-sm);
}

.message-bubble--assistant :deep(pre) {
  background: #1e1e2e;
  color: #cdd6f4;
  padding: var(--space-md);
  border-radius: var(--radius-sm);
  overflow-x: auto;
  font-size: 13px;
  font-family: var(--font-mono);
  margin: var(--space-sm) 0;
}

.message-bubble--assistant :deep(p) {
  margin: var(--space-xs) 0;
}

.message-bubble--assistant :deep(ul),
.message-bubble--assistant :deep(ol) {
  padding-left: var(--space-xl);
  margin: var(--space-sm) 0;
}

.assistant-row {
  display: flex;
  align-items: flex-start;
  gap: var(--space-sm);
  max-width: 75%;
}

.avatar {
  width: 28px;
  height: 28px;
  background: #eef2ff;
  color: var(--primary);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 11px;
  font-weight: 700;
  flex-shrink: 0;
}

/* Tool call card */
.tool-card {
  display: inline-flex;
  align-items: center;
  gap: var(--space-sm);
  padding: var(--space-sm) var(--space-lg);
  background: #eef2ff;
  border: 1px solid #c7d2fe;
  border-radius: 999px;
  font-size: 13px;
  color: var(--primary-dark);
}
.tool-card.completed {
  background: var(--success-light);
  border-color: #a7f3d0;
  color: #065f46;
}
.tool-card-icon {
  display: flex;
}
.tool-card-icon.spinning {
  animation: spin 2s linear infinite;
}
@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}
.tool-card-text {
  font-weight: 500;
}

/* System notice */
.system-notice {
  display: inline-flex;
  align-items: flex-start;
  gap: var(--space-sm);
  padding: var(--space-sm) var(--space-lg);
  font-size: 12px;
  color: var(--text-secondary);
  background: var(--border-light);
  border-radius: var(--radius-sm);
  max-width: 80%;
  word-break: break-word;
  line-height: 1.5;
}
.system-notice svg {
  flex-shrink: 0;
  margin-top: 2px;
  color: var(--muted);
}

/* Streaming */
.streaming-bar {
  display: inline-flex;
  align-items: center;
  gap: var(--space-sm);
  padding: var(--space-sm) var(--space-lg);
  font-size: 13px;
  color: var(--primary);
  font-weight: 500;
}
.streaming-pulse {
  width: 8px;
  height: 8px;
  background: var(--primary);
  border-radius: 50%;
  animation: pulse 1.5s ease-in-out infinite;
}
@keyframes pulse {
  0%, 100% { opacity: 0.4; transform: scale(0.8); }
  50% { opacity: 1; transform: scale(1.2); }
}
</style>
