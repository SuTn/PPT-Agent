<template>
  <div class="chat-interface">
    <header class="chat-header">
      <div v-if="session" class="chat-title">{{ session.title || session.session_id }}</div>
      <div class="chat-actions">
        <a
          v-if="session?.step === 'exported'"
          :href="`/api/v1/sessions/${sessionId}/download`"
          class="btn-download"
          download
        >下载 PPTX</a>
      </div>
    </header>
    <MessageList :messages="sessionStore.messages" :is-streaming="sessionStore.isStreaming" />
    <div class="chat-footer">
      <FileUpload :session-id="sessionId" @uploaded="onUploaded" />
      <InputBar :disabled="sessionStore.isStreaming" @send="onSend" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue";
import { useSessionsStore } from "../stores/sessions";
import { useSessionStore } from "../stores/session";
import MessageList from "./MessageList.vue";
import InputBar from "./InputBar.vue";
import FileUpload from "./FileUpload.vue";

const props = defineProps<{ sessionId: string }>();

const sessionsStore = useSessionsStore();
const sessionStore = useSessionStore(props.sessionId);
const session = computed(() => sessionsStore.current);

async function onSend(content: string) {
  await sessionStore.sendMessage(content);
  await sessionsStore.refreshCurrent();
}

function onUploaded(result: string) {
  sessionStore.addSystemNotice(result);
}
</script>

<style scoped>
.chat-interface {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.chat-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 20px;
  border-bottom: 1px solid var(--border);
}

.chat-title {
  font-size: 16px;
  font-weight: 600;
}

.btn-download {
  padding: 6px 16px;
  background: var(--primary);
  color: white;
  border-radius: 6px;
  text-decoration: none;
  font-size: 13px;
}

.chat-footer {
  border-top: 1px solid var(--border);
  padding: 12px 20px;
}
</style>
