<template>
  <div class="app-layout">
    <aside class="sidebar">
      <SessionList />
    </aside>
    <main class="main-area">
      <ChatInterface v-if="sessionsStore.currentId" :session-id="sessionsStore.currentId" :key="sessionsStore.currentId" />
      <div v-else class="empty-state">
        <p>选择或创建一个会话开始</p>
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
