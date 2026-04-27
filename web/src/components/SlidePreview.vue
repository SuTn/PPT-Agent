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
          <img
            v-if="slide.has_png"
            :src="`/api/v1/sessions/${sessionId}/slides/slide_${String(slide.page).padStart(2, '0')}_${slide.layout}.png`"
            :alt="`Slide ${slide.page}`"
            loading="lazy"
          />
          <div v-else class="thumb-placeholder">
            <span>{{ slide.page }}</span>
          </div>
          <div class="thumb-page">{{ slide.page }}</div>
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
        <img
          v-if="previewSlide.has_png"
          :src="`/api/v1/sessions/${sessionId}/slides/slide_${String(previewSlide.page).padStart(2, '0')}_${previewSlide.layout}.png`"
          :alt="`Slide ${previewSlide.page}`"
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from "vue";
import client from "../api/client";

const props = defineProps<{
  sessionId: string;
  step: string;
}>();

const slides = ref<any[]>([]);
const expanded = ref(true);
const previewSlide = ref<any>(null);

async function fetchSlides() {
  try {
    const { data } = await client.get(`/sessions/${props.sessionId}/slides`);
    slides.value = data.slides ?? [];
    if (slides.value.length > 0) {
      expanded.value = true;
    }
  } catch {
    // ignore
  }
}

watch(() => props.step, (val) => {
  if (val === "slides_done" || val === "exported") {
    fetchSlides();
  }
});

onMounted(() => {
  if (props.step === "slides_done" || props.step === "exported") {
    fetchSlides();
  }
});
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
  position: relative;
}
.thumb-wrapper img {
  width: 100%;
  display: block;
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
.preview-modal img {
  max-width: 100%;
  max-height: 85vh;
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
