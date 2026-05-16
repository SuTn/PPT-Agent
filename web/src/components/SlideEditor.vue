<template>
  <div class="slide-editor-overlay">
    <!-- Toolbar -->
    <div class="editor-toolbar">
      <button class="toolbar-btn" @click="confirmClose" title="关闭 (Esc)">
        <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
          <path d="M4 4l8 8M12 4l-8 8" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
        </svg>
      </button>
      <div class="toolbar-sep" />
      <button class="toolbar-btn" :disabled="currentIdx <= 0" @click="navigateTo(currentIdx - 1)" title="上一页">
        <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
          <path d="M9 3L5 7l4 4" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
      </button>
      <span class="toolbar-page">{{ currentSlide.page }} / {{ slides.length }}</span>
      <button class="toolbar-btn" :disabled="currentIdx >= slides.length - 1" @click="navigateTo(currentIdx + 1)" title="下一页">
        <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
          <path d="M5 3l4 4-4 4" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
      </button>
      <div class="toolbar-sep" />
      <div class="mode-toggle">
        <button :class="['mode-btn', { active: mode === 'visual' }]" @click="switchMode('visual')">可视化</button>
        <button :class="['mode-btn', { active: mode === 'source' }]" @click="switchMode('source')">源码</button>
      </div>
      <div class="toolbar-spacer" />
      <button class="toolbar-btn toolbar-btn-ghost" :disabled="!dirty" @click="revert" title="还原">还原</button>
      <button class="toolbar-btn toolbar-btn-primary" :disabled="!dirty || saving" @click="save">
        <span v-if="saving" class="spinner" />
        <span v-else>保存</span>
      </button>
    </div>

    <div class="editor-body">
      <!-- Sidebar: slide thumbnails -->
      <div class="editor-sidebar">
        <div
          v-for="(s, idx) in slides"
          :key="s.page"
          :class="['sidebar-thumb', { active: idx === currentIdx }]"
          @click="navigateTo(idx)"
        >
          <iframe
            v-if="s.filename"
            :src="`/api/v1/sessions/${sessionId}/slides/${s.filename}`"
            class="sidebar-iframe"
            sandbox=""
            loading="lazy"
          />
          <div class="sidebar-page">{{ s.page }}</div>
        </div>
      </div>

      <!-- Main editing area -->
      <div class="editor-main" ref="mainArea">
        <VisualEditor
          v-if="mode === 'visual'"
          ref="visualRef"
          :html="editedHtml"
          @update="onVisualUpdate"
        />
        <SourceEditor
          v-if="mode === 'source'"
          :html="editedHtml"
          @update="onSourceUpdate"
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from "vue";
import type { SlideInfo } from "../api/types";
import client from "../api/client";
import VisualEditor from "./VisualEditor.vue";
import SourceEditor from "./SourceEditor.vue";

const props = defineProps<{
  sessionId: string;
  slide: SlideInfo;
  slides: SlideInfo[];
}>();

const emit = defineEmits<{
  (e: "close"): void;
  (e: "saved", page: number): void;
}>();

const mode = ref<"visual" | "source">("visual");
const currentSlide = ref<SlideInfo>({ ...props.slide });
const originalHtml = ref("");
const editedHtml = ref("");
const dirty = ref(false);
const saving = ref(false);

const visualRef = ref<InstanceType<typeof VisualEditor> | null>(null);
const mainArea = ref<HTMLDivElement | null>(null);

const currentIdx = computed(() =>
  props.slides.findIndex((s) => s.page === currentSlide.value.page),
);

async function loadSlide(slide: SlideInfo) {
  if (!slide.filename) return;
  try {
    const resp = await fetch(`/api/v1/sessions/${props.sessionId}/slides/${slide.filename}`);
    const html = await resp.text();
    originalHtml.value = html;
    editedHtml.value = html;
    dirty.value = false;
  } catch {
    // ignore
  }
}

function onVisualUpdate(html: string) {
  editedHtml.value = html;
  dirty.value = html !== originalHtml.value;
}

function onSourceUpdate(html: string) {
  editedHtml.value = html;
  dirty.value = html !== originalHtml.value;
}

function switchMode(newMode: "visual" | "source") {
  mode.value = newMode;
}

async function save() {
  if (!dirty.value || saving.value) return;
  saving.value = true;
  try {
    // Get cleaned HTML from visual editor if in visual mode
    const htmlToSave = mode.value === "visual" && visualRef.value
      ? visualRef.value.getCleanedHtml()
      : editedHtml.value;

    await client.put(`/sessions/${props.sessionId}/slides/${currentSlide.value.filename}`, {
      html: htmlToSave,
    });
    originalHtml.value = htmlToSave;
    editedHtml.value = htmlToSave;
    dirty.value = false;
    emit("saved", currentSlide.value.page);
  } catch (err) {
    console.error("Save failed:", err);
  } finally {
    saving.value = false;
  }
}

function revert() {
  editedHtml.value = originalHtml.value;
  dirty.value = false;
}

async function navigateTo(idx: number) {
  if (idx < 0 || idx >= props.slides.length) return;
  if (dirty.value) {
    const ok = window.confirm("当前页面有未保存的修改，是否放弃？");
    if (!ok) return;
  }
  currentSlide.value = { ...props.slides[idx] };
  await loadSlide(currentSlide.value);
}

function confirmClose() {
  if (dirty.value) {
    const ok = window.confirm("当前页面有未保存的修改，是否放弃？");
    if (!ok) return;
  }
  emit("close");
}

function scaleIframe() {
  const area = mainArea.value;
  if (!area) return;
  const iframes = area.querySelectorAll<HTMLIFrameElement>(".visual-iframe, .preview-iframe");
  const availW = area.clientWidth - 40;
  const availH = area.clientHeight - 40;
  const scale = Math.min(availW / 1280, availH / 720, 1);
  iframes.forEach((el) => {
    el.style.transform = `scale(${scale})`;
  });
}

function onKeydown(e: KeyboardEvent) {
  // Ctrl+S / Cmd+S
  if ((e.ctrlKey || e.metaKey) && e.key === "s") {
    e.preventDefault();
    save();
    return;
  }
  // Skip keyboard nav when source editor is focused
  const tag = (e.target as HTMLElement)?.tagName;
  if (tag === "TEXTAREA" || tag === "INPUT") return;

  if (e.key === "ArrowLeft" && currentIdx.value > 0) {
    e.preventDefault();
    navigateTo(currentIdx.value - 1);
  } else if (e.key === "ArrowRight" && currentIdx.value < props.slides.length - 1) {
    e.preventDefault();
    navigateTo(currentIdx.value + 1);
  } else if (e.key === "Escape") {
    confirmClose();
  }
}

onMounted(async () => {
  await loadSlide(props.slide);
  document.addEventListener("keydown", onKeydown);
  await nextTick();
  scaleIframe();
  window.addEventListener("resize", scaleIframe);
});

onUnmounted(() => {
  document.removeEventListener("keydown", onKeydown);
  window.removeEventListener("resize", scaleIframe);
});

watch([mode, editedHtml], async () => {
  await nextTick();
  scaleIframe();
});
</script>

<style scoped>
.slide-editor-overlay {
  position: absolute;
  inset: 0;
  z-index: 90;
  background: var(--bg);
  display: flex;
  flex-direction: column;
}

/* ---- Toolbar ---- */
.editor-toolbar {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  padding: 0 var(--space-md);
  height: 44px;
  background: var(--card);
  border-bottom: 1px solid var(--border);
  flex-shrink: 0;
}
.toolbar-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  height: 30px;
  min-width: 30px;
  padding: 0 8px;
  border: none;
  border-radius: var(--radius-sm);
  background: transparent;
  color: var(--text);
  cursor: pointer;
  font-size: 13px;
  font-weight: 500;
}
.toolbar-btn:disabled {
  opacity: 0.35;
  cursor: not-allowed;
}
.toolbar-btn:hover:not(:disabled) {
  background: var(--border-light);
}
.toolbar-btn-primary {
  background: var(--primary);
  color: white;
}
.toolbar-btn-primary:hover:not(:disabled) {
  background: var(--primary-dark);
}
.toolbar-btn-ghost {
  color: var(--text-secondary);
}
.toolbar-sep {
  width: 1px;
  height: 20px;
  background: var(--border);
  margin: 0 var(--space-xs);
}
.toolbar-spacer {
  flex: 1;
}
.toolbar-page {
  font-size: 13px;
  color: var(--text-secondary);
  min-width: 40px;
  text-align: center;
  font-variant-numeric: tabular-nums;
}

/* ---- Mode toggle ---- */
.mode-toggle {
  display: flex;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  overflow: hidden;
}
.mode-btn {
  padding: 4px 14px;
  font-size: 13px;
  font-weight: 500;
  border: none;
  background: transparent;
  color: var(--text-secondary);
  cursor: pointer;
  transition: all var(--transition-fast);
}
.mode-btn.active {
  background: var(--primary);
  color: white;
}

/* ---- Body layout ---- */
.editor-body {
  display: flex;
  flex: 1;
  overflow: hidden;
}

/* ---- Sidebar ---- */
.editor-sidebar {
  width: 120px;
  flex-shrink: 0;
  background: var(--card);
  border-right: 1px solid var(--border);
  overflow-y: auto;
  padding: var(--space-sm);
  display: flex;
  flex-direction: column;
  gap: var(--space-sm);
}
.sidebar-thumb {
  position: relative;
  width: 100%;
  aspect-ratio: 16/9;
  border-radius: 4px;
  overflow: hidden;
  border: 2px solid transparent;
  cursor: pointer;
  transition: border-color var(--transition-fast);
}
.sidebar-thumb:hover {
  border-color: var(--primary-light);
}
.sidebar-thumb.active {
  border-color: var(--primary);
}
.sidebar-iframe {
  width: 1280px;
  height: 720px;
  transform: scale(0.0844);
  transform-origin: top left;
  border: none;
  pointer-events: none;
}
.sidebar-page {
  position: absolute;
  bottom: 2px;
  right: 2px;
  background: rgba(0, 0, 0, 0.5);
  color: white;
  font-size: 9px;
  padding: 0 4px;
  border-radius: 2px;
}

/* ---- Main editing area ---- */
.editor-main {
  flex: 1;
  display: flex;
  overflow: hidden;
}

/* ---- Spinner ---- */
.spinner {
  display: inline-block;
  width: 14px;
  height: 14px;
  border: 2px solid rgba(255,255,255,0.3);
  border-top-color: white;
  border-radius: 50%;
  animation: spin 0.6s linear infinite;
}
@keyframes spin {
  to { transform: rotate(360deg); }
}
</style>
