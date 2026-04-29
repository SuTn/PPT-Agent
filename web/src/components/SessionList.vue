<template>
  <div class="session-list">
    <div class="session-list-header">
      <div class="brand">
        <div class="brand-icon">P</div>
        <h2>PPT-Agent</h2>
      </div>
      <div class="header-actions">
        <button class="btn-templates" @click="showLibrary = true" title="模板库">
          <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
            <rect x="2" y="2" width="5" height="5" rx="1" stroke="currentColor" stroke-width="1.5"/>
            <rect x="9" y="2" width="5" height="5" rx="1" stroke="currentColor" stroke-width="1.5"/>
            <rect x="2" y="9" width="5" height="5" rx="1" stroke="currentColor" stroke-width="1.5"/>
            <rect x="9" y="9" width="5" height="5" rx="1" stroke="currentColor" stroke-width="1.5"/>
          </svg>
        </button>
        <button class="btn-new" @click="handleCreate" title="新建会话">
          <svg width="16" height="16" viewBox="0 0 16 16" fill="none"><path d="M8 3v10M3 8h10" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>
        </button>
      </div>
    </div>
    <ul>
      <li
        v-for="s in sessionsStore.sessions"
        :key="s.session_id"
        :class="{ active: s.session_id === sessionsStore.currentId }"
        @click="sessionsStore.currentId = s.session_id"
      >
        <div class="step-dot" :class="stepClass(s.step)"></div>
        <div class="session-info">
          <div class="session-title">{{ s.title || s.session_id }}</div>
          <div class="session-step">{{ stepLabel(s.step) }}</div>
        </div>
        <button class="btn-delete" @click.stop="handleDelete(s.session_id)" title="删除">
          <svg width="14" height="14" viewBox="0 0 14 14" fill="none"><path d="M3 3l8 8M11 3l-8 8" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/></svg>
        </button>
      </li>
    </ul>
    <TemplateLibrary :visible="showLibrary" @close="showLibrary = false" />
  </div>
</template>

<script setup lang="ts">
import { ref } from "vue";
import { useSessionsStore } from "../stores/sessions";
import type { Session } from "../api/types";
import TemplateLibrary from "./TemplateLibrary.vue";

const sessionsStore = useSessionsStore();
const showLibrary = ref(false);

const STEP_LABELS: Record<string, string> = {
  idle: "未开始",
  research_done: "研究完成",
  outline_done: "大纲完成",
  template_done: "模板已选",
  slides_done: "幻灯片完成",
  exported: "已导出",
};

function stepLabel(step: Session["step"]): string {
  return STEP_LABELS[step] ?? step;
}

function stepClass(step: Session["step"]): string {
  if (step === "exported") return "dot-success";
  if (step === "idle") return "dot-idle";
  return "dot-active";
}

async function handleCreate() {
  await sessionsStore.createSession();
}

async function handleDelete(id: string) {
  await sessionsStore.deleteSession(id);
}
</script>

<style scoped>
.session-list {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.session-list-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--space-lg) var(--space-xl);
  border-bottom: 1px solid var(--border);
}

.header-actions {
  display: flex;
  gap: var(--space-sm);
}

.btn-templates {
  background: none;
  border: 1px solid var(--border);
  color: var(--muted);
  cursor: pointer;
  padding: var(--space-xs);
  border-radius: var(--radius-sm);
  display: flex;
  align-items: center;
  justify-content: center;
}
.btn-templates:hover {
  color: var(--text);
  background: var(--border-light);
}

.brand {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
}

.brand-icon {
  width: 28px;
  height: 28px;
  background: var(--primary);
  color: white;
  border-radius: var(--radius-sm);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 15px;
  font-weight: 700;
}

.session-list-header h2 {
  font-size: 16px;
  font-weight: 700;
  color: var(--text);
}

.btn-new {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border: 1px solid var(--border);
  background: transparent;
  color: var(--text-secondary);
  border-radius: var(--radius-sm);
  cursor: pointer;
  transition: all var(--transition-fast);
}
.btn-new:hover {
  background: var(--primary);
  border-color: var(--primary);
  color: white;
}

ul {
  list-style: none;
  margin: 0;
  padding: var(--space-sm);
  overflow-y: auto;
  flex: 1;
}

li {
  padding: var(--space-md) var(--space-md);
  border-radius: var(--radius-md);
  cursor: pointer;
  margin-bottom: 2px;
  display: flex;
  align-items: center;
  gap: var(--space-md);
  transition: all var(--transition-fast);
  border-left: 3px solid transparent;
}
li:hover {
  background: var(--border-light);
}
li.active {
  background: #eef2ff;
  border-left-color: var(--primary);
}

.session-info {
  flex: 1;
  min-width: 0;
}

.session-title {
  font-size: 13px;
  font-weight: 500;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  color: var(--text);
}

.session-step {
  font-size: 11px;
  color: var(--muted);
  margin-top: 2px;
}

.step-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}
.dot-idle { background: var(--border); }
.dot-active { background: var(--primary-light); }
.dot-success { background: var(--success); }

.btn-delete {
  display: flex;
  align-items: center;
  justify-content: center;
  background: none;
  border: none;
  color: var(--muted);
  cursor: pointer;
  padding: var(--space-xs);
  border-radius: var(--radius-sm);
  opacity: 0;
  transition: all var(--transition-fast);
}
li:hover .btn-delete { opacity: 1; }
.btn-delete:hover {
  color: var(--danger);
  background: var(--danger-light);
}
</style>
