<template>
  <div class="research-preview" :class="{ expanded }">
    <!-- Header bar -->
    <div class="rp-header" @click="toggle">
      <div class="rp-icon-wrap">
        <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
          <path d="M4 2h7l5 5v7a2 2 0 01-2 2H4a2 2 0 01-2-2V4a2 2 0 012-2z" stroke="currentColor" stroke-width="1.3"/>
          <path d="M11 2v5h5" stroke="currentColor" stroke-width="1.3" stroke-linejoin="round"/>
          <path d="M6 10h6M6 13h4" stroke="currentColor" stroke-width="1.2" stroke-linecap="round"/>
        </svg>
      </div>
      <div class="rp-title-area">
        <span class="rp-label">Research Notes</span>
        <span class="rp-meta">{{ headingCount }} 个主题 · {{ content.length }} 字</span>
      </div>
      <div class="rp-toggle">
        <svg width="14" height="14" viewBox="0 0 14 14" fill="none"
          :style="{ transform: expanded ? 'rotate(180deg)' : '' }">
          <path d="M3 5l4 4 4-4" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
      </div>
    </div>

    <!-- Preview snippet (collapsed) -->
    <div v-if="!expanded" class="rp-snippet">
      <span class="rp-snippet-text">{{ snippet }}</span>
    </div>

    <!-- Full content (expanded) -->
    <div v-if="expanded" class="rp-body">
      <div class="rp-content" v-html="rendered"></div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from "vue";
import { marked } from "marked";
import DOMPurify from "dompurify";

const props = defineProps<{
  content: string;
}>();

const expanded = ref(true);

function toggle() {
  expanded.value = !expanded.value;
}

const rendered = computed(() => {
  if (!props.content) return "";
  const raw = marked.parse(props.content, { async: false }) as string;
  return DOMPurify.sanitize(raw);
});

const snippet = computed(() => {
  if (!props.content) return "";
  const text = props.content.replace(/^#+\s.*/gm, "").replace(/[*_`~]/g, "").trim();
  const first = text.split("\n").find(l => l.trim())?.trim() ?? "";
  return first.length > 120 ? first.slice(0, 120) + "…" : first;
});

const headingCount = computed(() => {
  const matches = props.content.match(/^#{1,3}\s.+/gm);
  return matches?.length ?? 0;
});
</script>

<style scoped>
.research-preview {
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  max-width: 600px;
  box-shadow:
    0 1px 2px rgba(0, 0, 0, 0.04),
    0 4px 16px rgba(79, 70, 229, 0.04);
  overflow: hidden;
  transition: box-shadow var(--transition-base);
}
.research-preview:hover {
  box-shadow:
    0 1px 2px rgba(0, 0, 0, 0.04),
    0 6px 20px rgba(79, 70, 229, 0.07);
}

/* ── Header ── */
.rp-header {
  display: flex;
  align-items: center;
  gap: var(--space-md);
  padding: var(--space-md) var(--space-lg);
  cursor: pointer;
  user-select: none;
  transition: background var(--transition-fast);
}
.rp-header:hover {
  background: var(--border-light);
}

.rp-icon-wrap {
  width: 34px;
  height: 34px;
  background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%);
  color: #92400e;
  border-radius: var(--radius-sm);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.rp-title-area {
  flex: 1;
  min-width: 0;
  display: flex;
  align-items: baseline;
  gap: var(--space-sm);
}

.rp-label {
  font-size: 13px;
  font-weight: 600;
  color: var(--text);
  letter-spacing: 0.02em;
}

.rp-meta {
  font-size: 11px;
  color: var(--muted);
  white-space: nowrap;
}

.rp-toggle {
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--muted);
  transition: transform var(--transition-fast);
  flex-shrink: 0;
}
.rp-toggle svg {
  transition: transform 200ms ease;
}

/* ── Snippet (collapsed) ── */
.rp-snippet {
  padding: 0 var(--space-lg) var(--space-md);
}

.rp-snippet-text {
  font-size: 12px;
  line-height: 1.6;
  color: var(--text-secondary);
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

/* ── Body (expanded) ── */
.rp-body {
  border-top: 1px solid var(--border-light);
}

.rp-content {
  padding: var(--space-lg);
  max-height: 420px;
  overflow-y: auto;
  font-size: 13px;
  line-height: 1.75;
  color: var(--text-secondary);
}

/* Markdown typography */
.rp-content :deep(h1) {
  display: none;
}

.rp-content :deep(h2) {
  font-size: 14px;
  font-weight: 600;
  color: var(--text);
  margin: 20px 0 6px;
  padding-bottom: 4px;
  border-bottom: 1px solid var(--border-light);
  letter-spacing: 0.01em;
}
.rp-content :deep(h2:first-child) {
  margin-top: 0;
}

.rp-content :deep(h3) {
  font-size: 13px;
  font-weight: 600;
  color: var(--text);
  margin: 14px 0 4px;
}

.rp-content :deep(p) {
  margin: 6px 0;
}

.rp-content :deep(ul),
.rp-content :deep(ol) {
  padding-left: 18px;
  margin: 4px 0;
}

.rp-content :deep(li) {
  margin: 2px 0;
}

.rp-content :deep(strong) {
  color: var(--text);
  font-weight: 600;
}

.rp-content :deep(blockquote) {
  border-left: 3px solid var(--primary-light);
  margin: 8px 0;
  padding: 4px 12px;
  color: var(--text-secondary);
  background: rgba(79, 70, 229, 0.02);
  border-radius: 0 var(--radius-sm) var(--radius-sm) 0;
}

.rp-content :deep(code) {
  font-family: var(--font-mono);
  font-size: 12px;
  background: var(--border-light);
  padding: 1px 5px;
  border-radius: 3px;
  color: var(--primary-dark);
}

.rp-content :deep(a) {
  color: var(--primary);
  text-decoration: none;
  border-bottom: 1px solid var(--primary-light);
  transition: border-color var(--transition-fast);
}
.rp-content :deep(a:hover) {
  border-bottom-color: var(--primary);
}
</style>
