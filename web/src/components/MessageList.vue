<template>
  <div class="message-list" ref="listRef">
    <div v-if="messages.length === 0" class="empty-hint">
      <p>输入你的 PPT 主题开始制作</p>
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
        <div v-if="msg.toolCalls" class="tool-call-badge">
          <span class="tool-icon">&#9881;</span>
          调用工具: {{ msg.toolCalls[0].name }}
        </div>
        <div v-else class="message-bubble message-bubble--assistant" v-html="renderMarkdown(msg.content)"></div>
      </template>
      <template v-else>
        <div class="system-notice">
          <span class="system-icon">&#9432;</span>
          <span v-html="renderMarkdown(msg.content)"></span>
        </div>
      </template>
    </div>
    <div v-if="isStreaming" class="streaming-indicator">
      <span class="dot"></span>
      <span class="dot"></span>
      <span class="dot"></span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, nextTick } from "vue";
import { marked } from "marked";
import type { Message } from "../api/types";

defineProps<{
  messages: Message[];
  isStreaming: boolean;
}>();

const listRef = ref<HTMLElement | null>(null);

function renderMarkdown(text: string): string {
  if (!text) return "";
  return marked.parse(text, { async: false }) as string;
}

watch(
  () => listRef.value,
  () => {
    nextTick(() => {
      if (listRef.value) {
        listRef.value.scrollTop = listRef.value.scrollHeight;
      }
    });
  },
  { immediate: true }
);
</script>

<style scoped>
.message-list {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.empty-hint {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--muted);
}

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
  justify-content: center;
}

.message-bubble {
  max-width: 75%;
  padding: 10px 14px;
  border-radius: 12px;
  line-height: 1.6;
  font-size: 14px;
  word-break: break-word;
}

.message-bubble--user {
  background: var(--primary);
  color: white;
  border-bottom-right-radius: 4px;
}

.message-bubble--assistant {
  background: var(--card);
  border: 1px solid var(--border);
  border-bottom-left-radius: 4px;
}

.message-bubble--assistant :deep(pre) {
  background: #1e1e2e;
  color: #cdd6f4;
  padding: 12px;
  border-radius: 8px;
  overflow-x: auto;
  font-size: 13px;
}

.tool-call-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  background: #ebf4ff;
  color: #2b6cb0;
  border-radius: 6px;
  font-size: 13px;
}

.tool-icon {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.system-notice {
  display: flex;
  align-items: flex-start;
  gap: 6px;
  padding: 8px 12px;
  font-size: 13px;
  color: var(--muted);
  background: var(--hover);
  border-radius: 6px;
  max-width: 80%;
  word-break: break-word;
}

.system-icon {
  flex-shrink: 0;
  margin-top: 2px;
}

.streaming-indicator {
  display: flex;
  gap: 4px;
  padding: 8px;
}

.dot {
  width: 6px;
  height: 6px;
  background: var(--muted);
  border-radius: 50%;
  animation: bounce 1.4s infinite ease-in-out both;
}

.dot:nth-child(1) { animation-delay: 0s; }
.dot:nth-child(2) { animation-delay: 0.16s; }
.dot:nth-child(3) { animation-delay: 0.32s; }

@keyframes bounce {
  0%, 80%, 100% { transform: scale(0); }
  40% { transform: scale(1); }
}
</style>
