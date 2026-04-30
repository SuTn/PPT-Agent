<template>
  <div class="chat-interface">
    <header class="chat-header">
      <div class="header-left">
        <div v-if="session" class="chat-title">{{ session.title || session.session_id }}</div>
      </div>
      <div class="header-actions">
        <button
          v-if="sessionStore.pipelineStep === 'slides_done' && !sessionStore.isStreaming"
          class="btn-export"
          :disabled="exporting"
          @click="onExport"
        >
          <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
            <path d="M7 2v7M4 6l3 3 3-3M2 11h10" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
          {{ exporting ? '导出中...' : '导出 PPTX' }}
        </button>
        <a
          v-if="session?.step === 'exported'"
          :href="`/api/v1/sessions/${sessionId}/download`"
          class="btn-download"
          download
        >
          <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
            <path d="M7 2v7M4 6l3 3 3-3M2 11h10" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
          下载 PPTX
        </a>
      </div>
    </header>
    <PipelineStepper :current-step="sessionStore.pipelineStep" />
    <MessageList :messages="sessionStore.messages" :is-streaming="sessionStore.isStreaming" :research-notes="sessionStore.researchNotes" @send="onSend" />
    <TemplateSelector
      v-if="showTemplateSelector"
      @select="onTemplateSelect"
    />
    <SlidePreview
      v-if="showSlidePreview"
      :session-id="sessionId"
      :slides="sessionStore.slides"
      :saved-page="savedPage"
      @edit="editingSlide = $event"
    />
    <SlideEditor
      v-if="editingSlide"
      :session-id="sessionId"
      :slide="editingSlide"
      :slides="sessionStore.slides"
      @close="editingSlide = null"
      @saved="onSlideSaved"
    />
    <div class="chat-footer">
      <FileUpload :session-id="sessionId" @uploaded="onUploaded" />
      <InputBar :disabled="sessionStore.isStreaming" @send="onSend" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { useSessionsStore } from "../stores/sessions";
import { useSessionStore } from "../stores/session";
import client from "../api/client";
import MessageList from "./MessageList.vue";
import PipelineStepper from "./PipelineStepper.vue";
import InputBar from "./InputBar.vue";
import FileUpload from "./FileUpload.vue";
import TemplateSelector from "./TemplateSelector.vue";
import SlidePreview from "./SlidePreview.vue";
import SlideEditor from "./SlideEditor.vue";
import type { SlideInfo } from "../api/types";

const props = defineProps<{ sessionId: string }>();

const sessionsStore = useSessionsStore();
const sessionStore = useSessionStore(props.sessionId);
const session = computed(() => sessionsStore.current);

const showTemplateSelector = computed(() => {
  const step = sessionStore.pipelineStep;
  return step === "outline_done" && !sessionStore.isStreaming;
});

const showSlidePreview = computed(() => {
  return sessionStore.slides.length > 0 || sessionStore.pipelineStep === "slides_done" || sessionStore.pipelineStep === "exported";
});

onMounted(() => {
  sessionStore.loadHistory();
});

async function onSend(content: string) {
  await sessionStore.sendMessage(content);
  await sessionsStore.refreshCurrent();
}

async function onTemplateSelect(key: string) {
  await sessionStore.sendMessage(`使用 ${key} 模板`);
  await sessionsStore.refreshCurrent();
}

function onUploaded(result: string) {
  sessionStore.addSystemNotice(result);
}

const exporting = ref(false);
const editingSlide = ref<SlideInfo | null>(null);
const savedPage = ref<number | null>(null);
async function onExport() {
  exporting.value = true;
  try {
    await client.post(`/sessions/${props.sessionId}/export`);
    await sessionsStore.refreshCurrent();
  } finally {
    exporting.value = false;
  }
}

async function onSlideSaved(page: number) {
  savedPage.value = page;
  await sessionStore.refreshSlides();
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
  padding: var(--space-md) var(--space-xl);
  border-bottom: 1px solid var(--border);
  background: var(--card);
}

.header-left {
  display: flex;
  align-items: center;
  gap: var(--space-md);
}

.chat-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--text);
}

.btn-export {
  display: inline-flex;
  align-items: center;
  gap: var(--space-sm);
  padding: var(--space-sm) var(--space-lg);
  background: var(--primary);
  color: white;
  border: none;
  border-radius: var(--radius-md);
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: opacity var(--transition-fast);
}
.btn-export:hover:not(:disabled) {
  opacity: 0.9;
}
.btn-export:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-download {
  display: inline-flex;
  align-items: center;
  gap: var(--space-sm);
  padding: var(--space-sm) var(--space-lg);
  background: var(--success);
  color: white;
  border-radius: var(--radius-md);
  text-decoration: none;
  font-size: 13px;
  font-weight: 500;
  transition: opacity var(--transition-fast);
}
.btn-download:hover {
  opacity: 0.9;
}

.chat-footer {
  border-top: 1px solid var(--border);
  background: var(--card);
}
</style>
