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
        <button class="preview-close" @click="previewSlide = null">
          <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
            <path d="M4 4l8 8M12 4l-8 8" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
          </svg>
        </button>
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
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from "vue";
import type { SlideInfo } from "../api/types";
import client from "../api/client";

const props = defineProps<{
  sessionId: string;
  slides: SlideInfo[];
}>();

const emit = defineEmits<{
  (e: "retry", page: number): void;
}>();

const expanded = ref(true);
const previewSlide = ref<SlideInfo | null>(null);
const retryingPage = ref<number | null>(null);
const slideVersions = reactive<Record<number, number>>({});

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
  background: rgba(0, 0, 0, 0.6);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 100;
}

.preview-modal {
  position: relative;
  max-width: 90vw;
  max-height: 90vh;
}
.preview-iframe {
  width: 1280px;
  height: 720px;
  max-width: 90vw;
  max-height: 85vh;
  border: none;
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-lg);
}
.preview-placeholder {
  width: 640px;
  height: 360px;
  background: var(--card);
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--muted);
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-lg);
}

.preview-close {
  position: absolute;
  top: -32px;
  right: 0;
  width: 28px;
  height: 28px;
  background: rgba(255, 255, 255, 0.9);
  border: none;
  border-radius: 50%;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text);
}
</style>
