<template>
  <div class="research-preview" v-if="content">
    <div class="research-header" @click="toggle">
      <div class="research-icon">
        <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
          <path d="M6 2h4l4 4v6a2 2 0 01-2 2H6a2 2 0 01-2-2V4a2 2 0 012-2z" stroke="currentColor" stroke-width="1.2" fill="none"/>
          <path d="M6 2v4h4" stroke="currentColor" stroke-width="1.2" fill="none"/>
          <circle cx="8" cy="10" r="1.5" stroke="currentColor" stroke-width="1"/>
        </svg>
      </div>
      <div class="research-title-row">
        <span class="research-label">研究笔记</span>
        <span class="research-toggle">{{ expanded ? '收起' : '展开' }}</span>
      </div>
    </div>
    <div v-if="expanded" class="research-body" v-html="rendered"></div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from "vue";
import { marked } from "marked";
import DOMPurify from "dompurify";

const props = defineProps<{
  content: string;
}>();

const expanded = ref(false);

function toggle() {
  expanded.value = !expanded.value;
}

const rendered = computed(() => {
  if (!props.content) return "";
  const raw = marked.parse(props.content, { async: false }) as string;
  return DOMPurify.sanitize(raw);
});
</script>

<style scoped>
.research-preview {
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  max-width: 560px;
  box-shadow: var(--shadow-sm);
  overflow: hidden;
}

.research-header {
  display: flex;
  align-items: center;
  gap: var(--space-md);
  padding: var(--space-md) var(--space-lg);
  cursor: pointer;
  user-select: none;
  transition: background var(--transition-fast);
}
.research-header:hover {
  background: var(--border-light);
}

.research-icon {
  width: 32px; height: 32px;
  background: #fef3c7;
  color: #92400e;
  border-radius: var(--radius-sm);
  display: flex; align-items: center; justify-content: center;
  flex-shrink: 0;
}

.research-title-row {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.research-label {
  font-size: 14px;
  font-weight: 600;
  color: var(--text);
}

.research-toggle {
  font-size: 12px;
  color: var(--primary);
  font-weight: 500;
}

.research-body {
  padding: 0 var(--space-lg) var(--space-lg);
  border-top: 1px solid var(--border-light);
  max-height: 400px;
  overflow-y: auto;
  font-size: 13px;
  line-height: 1.6;
  color: var(--text-secondary);
}

.research-body :deep(h1) {
  display: none;
}
.research-body :deep(h2) {
  font-size: 14px;
  font-weight: 600;
  color: var(--text);
  margin: var(--space-md) 0 var(--space-xs);
}
.research-body :deep(h3) {
  font-size: 13px;
  font-weight: 600;
  color: var(--text);
  margin: var(--space-sm) 0 2px;
}
.research-body :deep(ul) {
  padding-left: var(--space-md);
  margin: 2px 0;
}
.research-body :deep(li) {
  margin: 1px 0;
}
.research-body :deep(strong) {
  color: var(--text);
}
.research-body :deep(p) {
  margin: var(--space-xs) 0;
}
</style>
