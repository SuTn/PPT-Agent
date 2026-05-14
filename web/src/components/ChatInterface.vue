<template>
  <div class="chat-interface">
    <header class="chat-header">
      <div class="header-left">
        <div v-if="session" class="chat-title">{{ session.title || session.session_id }}</div>
        <div
          v-if="currentTemplate && !showTemplateSelector"
          class="template-badge"
          @click="showChangeTemplate = true"
        >
          <span class="badge-color" :style="{ background: currentTemplate.colors.primary }"></span>
          <span class="badge-name">{{ currentTemplate.name }}</span>
          <svg class="badge-icon" width="12" height="12" viewBox="0 0 12 12" fill="none">
            <path d="M9 1.5l1.5 1.5-7 7H2v-1.5l7-7z" stroke="currentColor" stroke-width="1" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
        </div>
      </div>
      <div class="header-actions">
        <div
          v-if="sessionStore.pipelineStep === 'slides_done' && !sessionStore.isStreaming"
          class="btn-export-group"
        >
          <button
            class="btn-export"
            :disabled="exporting"
            @click="onExport"
          >
            <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
              <path d="M7 2v7M4 6l3 3 3-3M2 11h10" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
            <template v-if="exporting">{{ exportProgress || '导出中...' }}</template>
            <template v-else>{{ exportMode === 'editable' ? '可编辑 PPTX' : '图片 PPTX' }}</template>
          </button>
          <button
            class="btn-export-toggle"
            :disabled="exporting"
            @click.stop="showExportMenu = !showExportMenu"
          >
            <svg width="10" height="6" viewBox="0 0 10 6" fill="none">
              <path d="M1 1l4 4 4-4" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
          </button>
          <div v-if="showExportMenu" class="export-dropdown" @click.stop>
            <button class="export-dropdown-item" :class="{ active: exportMode === 'editable' }" @click="setExportMode('editable')">
              可编辑 PPTX
              <span class="export-dropdown-desc">文字可直接编辑</span>
            </button>
            <button class="export-dropdown-item" :class="{ active: exportMode === 'image' }" @click="setExportMode('image')">
              图片 PPTX
              <span class="export-dropdown-desc">高保真图片格式</span>
            </button>
          </div>
        </div>
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
    <PipelineStepper :current-step="sessionStore.pipelineStep" :template="currentTemplate" @change-template="showChangeTemplate = true" />
    <div v-if="showTemplateSelector" class="template-area">
      <TemplateSelector @select="onTemplateSelect" />
    </div>
    <MessageList v-else :messages="sessionStore.messages" :is-streaming="sessionStore.isStreaming" :research-notes="sessionStore.researchNotes" :outline="sessionStore.outline" @send="onSend" />
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
    <div class="chat-footer" v-if="!showTemplateSelector">
      <FileUpload :session-id="sessionId" @uploaded="onUploaded" />
      <InputBar :disabled="sessionStore.isStreaming" v-model:mode="sessionStore.mode" @send="onSend" />
    </div>

    <!-- Change template modal -->
    <div v-if="showChangeTemplate" class="modal-overlay" @click.self="showChangeTemplate = false">
      <div class="modal-content">
        <div class="modal-header">
          <span class="modal-title">更换模板</span>
          <button class="modal-close" @click="showChangeTemplate = false">&times;</button>
        </div>
        <TemplateSelector @select="onChangeTemplate" />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from "vue";
import { useSessionsStore } from "../stores/sessions";
import { useSessionStore } from "../stores/session";
import client from "../api/client";
import { exportEditablePptx } from "../export/editableExport";
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
  return sessionStore.pipelineStep === "idle" && !sessionStore.isStreaming;
});

const showSlidePreview = computed(() => {
  return sessionStore.slides.length > 0 || sessionStore.pipelineStep === "slides_done" || sessionStore.pipelineStep === "exported";
});

const currentTemplate = ref<{ key: string; name: string; description: string; colors: Record<string, string> } | null>(null);
const showChangeTemplate = ref(false);

onMounted(async () => {
  await sessionStore.loadHistory();
  document.addEventListener('click', onClickOutside);

  // Restore current template info from session data
  const s = sessionsStore.current;
  if (s?.template_key && sessionStore.pipelineStep !== "idle") {
    try {
      const { data } = await client.get("/templates");
      currentTemplate.value = data.templates?.find((t: any) => t.key === s.template_key) ?? null;
    } catch { /* ignore */ }
  }
});

async function onSend(content: string) {
  await sessionStore.sendMessage(content);
  await sessionsStore.refreshCurrent();
}

async function onTemplateSelect(template: { key: string; name: string; description: string; colors: Record<string, string> }) {
  try {
    await client.patch(`/sessions/${props.sessionId}/template`, { template_key: template.key });
    currentTemplate.value = template;
    sessionStore.pipelineStep = "template_done";
    await sessionsStore.refreshCurrent();
  } catch (e) {
    console.error("Template selection failed:", e);
  }
}

async function onChangeTemplate(template: { key: string; name: string; description: string; colors: Record<string, string> }) {
  try {
    await client.patch(`/sessions/${props.sessionId}/template`, { template_key: template.key });
    currentTemplate.value = template;
    sessionStore.pipelineStep = "template_done";
    showChangeTemplate.value = false;
    await sessionsStore.refreshCurrent();
  } catch (e) {
    console.error("Template change failed:", e);
  }
}

function onUploaded(result: string) {
  sessionStore.addSystemNotice(result);
}

const exporting = ref(false);
const editingSlide = ref<SlideInfo | null>(null);
const savedPage = ref<number | null>(null);
const exportMode = ref<'editable' | 'image'>('editable');
const showExportMenu = ref(false);
const exportProgress = ref<string | null>(null);

function setExportMode(mode: 'editable' | 'image') {
  exportMode.value = mode;
  showExportMenu.value = false;
}

function onClickOutside() {
  showExportMenu.value = false;
}

onUnmounted(() => {
  document.removeEventListener('click', onClickOutside);
});

async function onExport() {
  exporting.value = true;
  exportProgress.value = null;
  try {
    if (exportMode.value === 'editable') {
      const session = sessionsStore.current;
      const fileName = (session?.title || props.sessionId).replace(/[/\\:*?"<>|]/g, '_');
      await exportEditablePptx(
        props.sessionId,
        sessionStore.slides,
        fileName,
        (msg) => { exportProgress.value = msg; }
      );
    } else {
      await client.post(`/sessions/${props.sessionId}/export`);
      await sessionsStore.refreshCurrent();
    }
  } finally {
    exporting.value = false;
    exportProgress.value = null;
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

.template-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 4px 10px;
  background: var(--bg);
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  cursor: pointer;
  font-size: 12px;
  color: var(--text-secondary);
  transition: all var(--transition-fast);
}
.template-badge:hover {
  border-color: var(--primary-light);
  background: var(--card);
}

.badge-color {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  flex-shrink: 0;
}

.badge-name {
  font-weight: 500;
}

.badge-icon {
  color: var(--muted);
}

.btn-export-group {
  position: relative;
  display: inline-flex;
}

.btn-export-group .btn-export {
  border-radius: var(--radius-md) 0 0 var(--radius-md);
}

.btn-export-toggle {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: var(--space-sm) var(--space-sm);
  background: var(--primary);
  color: white;
  border: none;
  border-left: 1px solid rgba(255,255,255,0.3);
  border-radius: 0 var(--radius-md) var(--radius-md) 0;
  cursor: pointer;
  transition: opacity var(--transition-fast);
}
.btn-export-toggle:hover:not(:disabled) {
  opacity: 0.9;
}
.btn-export-toggle:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.export-dropdown {
  position: absolute;
  top: 100%;
  right: 0;
  margin-top: 4px;
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  box-shadow: 0 4px 12px rgba(0,0,0,0.15);
  z-index: 100;
  min-width: 180px;
  overflow: hidden;
}

.export-dropdown-item {
  display: flex;
  flex-direction: column;
  width: 100%;
  padding: 10px 14px;
  border: none;
  background: none;
  text-align: left;
  font-size: 13px;
  font-weight: 500;
  color: var(--text);
  cursor: pointer;
  transition: background var(--transition-fast);
}
.export-dropdown-item:hover {
  background: var(--bg);
}
.export-dropdown-item.active {
  color: var(--primary);
}
.export-dropdown-desc {
  font-size: 11px;
  font-weight: 400;
  color: var(--text-light);
  margin-top: 2px;
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

.template-area {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--chat-bg);
}

.chat-footer {
  border-top: 1px solid var(--border);
  background: var(--card);
}

/* Change template modal */
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 200;
}

.modal-content {
  background: var(--card);
  border-radius: var(--radius-lg);
  width: 90%;
  max-width: 820px;
  max-height: 85vh;
  overflow-y: auto;
  box-shadow: var(--shadow-lg);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--space-md) var(--space-xl);
  border-bottom: 1px solid var(--border);
}

.modal-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--text);
}

.modal-close {
  background: none;
  border: none;
  font-size: 22px;
  color: var(--muted);
  cursor: pointer;
  padding: 0 4px;
  line-height: 1;
  transition: color var(--transition-fast);
}
.modal-close:hover {
  color: var(--text);
}
</style>
