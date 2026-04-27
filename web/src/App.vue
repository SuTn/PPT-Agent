<template>
  <div class="app-layout">
    <aside class="sidebar">
      <SessionList />
    </aside>
    <main class="main-area">
      <ChatInterface v-if="sessionsStore.currentId" :session-id="sessionsStore.currentId" :key="sessionsStore.currentId" />
      <div v-else class="empty-state">
        <div class="hero-icon">P</div>
        <h3>PPT-Agent</h3>
        <p>AI 驱动的演示文稿生成工具</p>
        <button class="btn-primary" @click="sessionsStore.createSession()">
          <svg width="16" height="16" viewBox="0 0 16 16" fill="none"><path d="M8 3v10M3 8h10" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>
          开始制作
        </button>
      </div>
    </main>
  </div>
</template>

<script setup lang="ts">
import { onMounted } from "vue";
import { useSessionsStore } from "./stores/sessions";
import SessionList from "./components/SessionList.vue";
import ChatInterface from "./components/ChatInterface.vue";

const sessionsStore = useSessionsStore();

onMounted(async () => {
  await sessionsStore.fetchSessions();
  if (!sessionsStore.currentId && sessionsStore.sessions.length > 0) {
    sessionsStore.currentId = sessionsStore.sessions[0].session_id;
  }
});
</script>

<style scoped>
.hero-icon {
  width: 64px;
  height: 64px;
  background: var(--primary);
  color: white;
  border-radius: var(--radius-xl);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 28px;
  font-weight: 800;
}
.empty-state h3 {
  font-size: 20px;
  font-weight: 700;
  color: var(--text);
}
.empty-state p {
  font-size: 14px;
  color: var(--muted);
  margin-top: -var(--space-sm);
}
</style>
