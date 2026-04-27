<template>
  <div class="session-list">
    <div class="session-list-header">
      <h2>PPT-Agent</h2>
      <button class="btn-new" @click="handleCreate">+ 新建</button>
    </div>
    <ul>
      <li
        v-for="s in sessionsStore.sessions"
        :key="s.session_id"
        :class="{ active: s.session_id === sessionsStore.currentId }"
        @click="sessionsStore.currentId = s.session_id"
      >
        <div class="session-title">{{ s.title || s.session_id }}</div>
        <div class="session-step">{{ stepLabel(s.step) }}</div>
        <button class="btn-delete" @click.stop="handleDelete(s.session_id)" title="删除">×</button>
      </li>
    </ul>
  </div>
</template>

<script setup lang="ts">
import { useSessionsStore } from "../stores/sessions";
import type { Session } from "../api/types";

const sessionsStore = useSessionsStore();

function stepLabel(step: Session["step"]): string {
  const map: Record<string, string> = {
    idle: "未开始",
    outline_done: "大纲完成",
    template_done: "模板已选",
    slides_done: "幻灯片完成",
    exported: "已导出",
  };
  return map[step] ?? step;
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
  padding: 16px;
  border-bottom: 1px solid var(--border);
}

.session-list-header h2 {
  margin: 0;
  font-size: 18px;
}

.btn-new {
  padding: 6px 12px;
  border: 1px solid var(--primary);
  background: transparent;
  color: var(--primary);
  border-radius: 6px;
  cursor: pointer;
  font-size: 13px;
}

.btn-new:hover {
  background: var(--primary);
  color: white;
}

ul {
  list-style: none;
  margin: 0;
  padding: 8px;
  overflow-y: auto;
  flex: 1;
}

li {
  padding: 10px 12px;
  border-radius: 8px;
  cursor: pointer;
  margin-bottom: 4px;
  display: flex;
  align-items: center;
  gap: 8px;
  transition: background 0.15s;
}

li:hover {
  background: var(--hover);
}

li.active {
  background: var(--active);
}

.session-title {
  flex: 1;
  font-size: 14px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.session-step {
  font-size: 11px;
  color: var(--muted);
  white-space: nowrap;
}

.btn-delete {
  background: none;
  border: none;
  color: var(--muted);
  cursor: pointer;
  font-size: 16px;
  padding: 0 4px;
  line-height: 1;
  opacity: 0;
  transition: opacity 0.15s;
}

li:hover .btn-delete {
  opacity: 1;
}

.btn-delete:hover {
  color: #e53e3e;
}
</style>
