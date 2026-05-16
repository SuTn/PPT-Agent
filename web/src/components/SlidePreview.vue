<template>
  <div class="slide-preview" v-if="slides.length > 0">
    <div class="preview-header" @click="expanded = !expanded">
      <span class="preview-label">
        <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
          <rect x="1" y="1" width="5" height="5" rx="1" stroke="currentColor" stroke-width="1.2"/>
          <rect x="8" y="1" width="5" height="5" rx="1" stroke="currentColor" stroke-width="1.2"/>
          <rect x="1" y="8" width="5" height="5" rx="1" stroke="currentColor" stroke-width="1.2"/>
          <rect x="8" y="8" width="5" height="5" rx="1" stroke="currentColor" stroke-width="1.2"/>
        </svg>
        幻灯片预览 ({{ slides.length }} 页)
      </span>
      <svg :class="['chevron', { expanded }]" width="16" height="16" viewBox="0 0 16 16" fill="none">
        <path d="M4 6l4 4 4-4" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
      </svg>
    </div>
    <div v-if="expanded" class="slide-grid">
      <div v-for="slide in slides" :key="slide.page" class="slide-thumb" @click="previewSlide = slide">
        <div class="thumb-wrapper">
          <iframe
            v-if="slide.filename"
            :key="`thumb-${slide.page}-${slideVersions[slide.page] ?? 0}`"
            :src="slideSrc(slide)"
            class="thumb-iframe"
            sandbox=""
            loading="lazy"
          />
          <div v-else class="thumb-placeholder">
            <span>{{ slide.page }}</span>
          </div>
          <div class="thumb-page">{{ slide.page }}</div>
          <button
            class="btn-edit"
            @click.stop="$emit('edit', slide)"
            title="编辑"
          >
            <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
              <path d="M8.5 1.5l2 2-7 7H1.5V8.5l7-7z" stroke="currentColor" stroke-width="1.2" stroke-linejoin="round"/>
            </svg>
          </button>
          <button
            class="btn-retry"
            :disabled="retryingPage === slide.page"
            @click.stop="retrySlide(slide.page)"
            title="重新生成"
          >
            <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
              <path d="M1 6a5 5 0 1 1 1 3" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
              <path d="M1 9V6h3" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
          </button>
        </div>
      </div>
    </div>
    <div v-if="previewSlide" class="preview-overlay" @click.self="previewSlide = null">
      <div class="preview-modal">
        <div class="preview-toolbar">
          <span class="preview-counter">{{ previewIndex + 1 }} / {{ slides.length }}</span>
          <div class="preview-toolbar-actions">
            <button class="preview-btn" @click="$emit('edit', previewSlide); previewSlide = null" title="编辑">
              <svg width="14" height="14" viewBox="0 0 12 12" fill="none">
                <path d="M8.5 1.5l2 2-7 7H1.5V8.5l7-7z" stroke="currentColor" stroke-width="1.2" stroke-linejoin="round"/>
              </svg>
            </button>
            <button class="preview-btn" @click="previewSlide = null" title="关闭 (Esc)">
              <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
                <path d="M4 4l6 6M10 4l-6 6" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
              </svg>
            </button>
          </div>
        </div>
        <div class="preview-body">
          <button
            v-if="previewIndex > 0"
            class="nav-btn nav-prev"
            @click="navigatePreview(-1)"
            title="上一页 (←)"
          >
            <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
              <path d="M12 5l-5 5 5 5" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
          </button>
          <div class="preview-frame">
            <iframe
              v-if="previewSlide.filename"
              :key="`preview-${previewSlide.page}-${slideVersions[previewSlide.page] ?? 0}`"
              :src="slideSrc(previewSlide)"
              class="preview-iframe"
              sandbox="allow-same-origin"
            />
            <div v-else class="preview-placeholder">
              <span>第 {{ previewSlide.page }} 页 — {{ previewSlide.layout }}</span>
            </div>
          </div>
          <button
            v-if="previewIndex < slides.length - 1"
            class="nav-btn nav-next"
            @click="navigatePreview(1)"
            title="下一页 (→)"
          >
            <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
              <path d="M8 5l5 5-5 5" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, watch, computed, onMounted, onUnmounted } from "vue";
import type { SlideInfo } from "../api/types";
import client from "../api/client";

const props = defineProps<{
  sessionId: string;
  slides: SlideInfo[];
  savedPage?: number | null;
}>();

watch(() => props.savedPage, (page) => {
  if (page != null) {
    slideVersions[page] = (slideVersions[page] ?? 0) + 1;
  }
});

const emit = defineEmits<{
  (e: "retry", page: number): void;
  (e: "edit", slide: SlideInfo): void;
}>();

const expanded = ref(true);
const previewSlide = ref<SlideInfo | null>(null);
const retryingPage = ref<number | null>(null);
const slideVersions = reactive<Record<number, number>>({});

const previewIndex = computed(() => {
  if (!previewSlide.value) return 0;
  return props.slides.findIndex(s => s.page === previewSlide.value!.page);
});

function navigatePreview(delta: number) {
  if (!previewSlide.value) return;
  const idx = previewIndex.value + delta;
  if (idx >= 0 && idx < props.slides.length) {
    previewSlide.value = props.slides[idx];
  }
}

function onKeydown(e: KeyboardEvent) {
  if (!previewSlide.value) return;
  if (e.key === "ArrowLeft") {
    e.preventDefault();
    navigatePreview(-1);
  } else if (e.key === "ArrowRight") {
    e.preventDefault();
    navigatePreview(1);
  } else if (e.key === "Escape") {
    e.preventDefault();
    previewSlide.value = null;
  }
}

onMounted(() => window.addEventListener("keydown", onKeydown));
onUnmounted(() => window.removeEventListener("keydown", onKeydown));

function slideSrc(slide: SlideInfo): string {
  const v = slideVersions[slide.page] ?? 0;
  const sep = v > 0 ? `?v=${v}` : "";
  return `/api/v1/sessions/${props.sessionId}/slides/${slide.filename}${sep}`;
}

async function retrySlide(page: number) {
  retryingPage.value = page;
  try {
    await client.post(`/sessions/${props.sessionId}/slides/${page}/retry`);
    slideVersions[page] = (slideVersions[page] ?? 0) + 1;
    emit("retry", page);
  } finally {
    retryingPage.value = null;
  }
}
</script>

<style scoped>
.slide-preview {
  background: var(--card);
  border-top: 1px solid var(--border);
}

.preview-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--space-md) var(--space-xl);
  cursor: pointer;
  user-select: none;
}
.preview-header:hover {
  background: var(--border-light);
}

.preview-label {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  font-size: 13px;
  font-weight: 600;
  color: var(--text);
}

.chevron {
  color: var(--muted);
  transition: transform var(--transition-fast);
}
.chevron.expanded {
  transform: rotate(180deg);
}

.slide-grid {
  display: flex;
  gap: var(--space-md);
  padding: 0 var(--space-xl) var(--space-lg);
  overflow-x: auto;
}

.slide-thumb {
  flex-shrink: 0;
  cursor: pointer;
  border-radius: var(--radius-sm);
  overflow: hidden;
  border: 2px solid var(--border);
  transition: all var(--transition-fast);
}
.slide-thumb:hover {
  border-color: var(--primary-light);
  box-shadow: var(--shadow-md);
}

.thumb-wrapper {
  width: 140px;
  aspect-ratio: 16/9;
  position: relative;
  overflow: hidden;
}
.thumb-iframe {
  width: 1280px;
  height: 720px;
  transform: scale(0.109375);
  transform-origin: top left;
  border: none;
  pointer-events: none;
}

.thumb-placeholder {
  width: 100%;
  aspect-ratio: 16/9;
  background: var(--border-light);
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--muted);
  font-weight: 600;
}

.thumb-page {
  position: absolute;
  bottom: 4px;
  right: 4px;
  background: rgba(0, 0, 0, 0.5);
  color: white;
  font-size: 10px;
  padding: 1px 6px;
  border-radius: 3px;
}

.btn-edit {
  position: absolute;
  top: 4px;
  left: 4px;
  width: 22px;
  height: 22px;
  padding: 0;
  border: none;
  border-radius: 4px;
  background: rgba(0, 0, 0, 0.5);
  color: white;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0;
  transition: opacity var(--transition-fast);
}
.slide-thumb:hover .btn-edit {
  opacity: 1;
}
.btn-edit:hover {
  background: var(--info);
}

.btn-retry {
  position: absolute;
  top: 4px;
  right: 4px;
  width: 22px;
  height: 22px;
  padding: 0;
  border: none;
  border-radius: 4px;
  background: rgba(0, 0, 0, 0.5);
  color: white;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0;
  transition: opacity var(--transition-fast);
}
.slide-thumb:hover .btn-retry {
  opacity: 1;
}
.btn-retry:hover:not(:disabled) {
  background: var(--primary);
}
.btn-retry:disabled {
  opacity: 1;
  background: rgba(0, 0, 0, 0.3);
  cursor: not-allowed;
}

.preview-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 100;
}

.preview-modal {
  position: relative;
  max-width: 94vw;
}

.preview-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
  padding: 0 4px;
}

.preview-counter {
  font-size: 13px;
  font-weight: 500;
  color: rgba(255, 255, 255, 0.8);
  font-variant-numeric: tabular-nums;
}

.preview-toolbar-actions {
  display: flex;
  gap: 4px;
}

.preview-btn {
  width: 30px;
  height: 30px;
  background: rgba(255, 255, 255, 0.12);
  border: none;
  border-radius: var(--radius-sm);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  color: rgba(255, 255, 255, 0.8);
  transition: all var(--transition-fast);
}
.preview-btn:hover {
  background: rgba(255, 255, 255, 0.25);
  color: #fff;
}

.preview-body {
  display: flex;
  align-items: center;
  gap: 12px;
}

.preview-frame {
  border-radius: var(--radius-md);
  overflow: hidden;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4);
}

.preview-iframe {
  width: 1280px;
  height: 720px;
  max-width: min(90vw, calc(94vw - 96px));
  max-height: 85vh;
  border: none;
  display: block;
}
.preview-placeholder {
  width: 640px;
  height: 360px;
  background: var(--card);
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--muted);
}

.nav-btn {
  width: 40px;
  height: 40px;
  background: rgba(255, 255, 255, 0.12);
  border: none;
  border-radius: 50%;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  color: rgba(255, 255, 255, 0.85);
  transition: all var(--transition-fast);
  flex-shrink: 0;
}
.nav-btn:hover {
  background: rgba(255, 255, 255, 0.25);
  color: #fff;
  transform: scale(1.08);
}
</style>
