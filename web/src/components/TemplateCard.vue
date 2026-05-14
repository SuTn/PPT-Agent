<template>
  <div class="template-card" :class="{ selected }" @click="$emit('select', template.key)">
    <div class="card-preview" :style="previewBg">
      <div class="preview-header-bar" :style="headerBarBg"></div>
      <div class="preview-body">
        <div class="preview-line" :style="lineBg"></div>
        <div class="preview-line w75" :style="lineBg"></div>
        <div class="preview-line w50" :style="lineBg"></div>
      </div>
      <div class="preview-accent" :style="accentBg"></div>
    </div>
    <div class="card-body">
      <div class="card-name">{{ template.name }}</div>
      <div class="card-desc">{{ template.description }}</div>
      <div class="card-colors">
        <span v-for="c in paletteColors" :key="c" class="color-dot" :style="{ background: c }"></span>
      </div>
    </div>
    <div v-if="selected" class="check-badge">
      <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
        <circle cx="10" cy="10" r="10" fill="var(--primary)" />
        <path d="M6 10l3 3 5-5" stroke="white" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" />
      </svg>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue";

const props = defineProps<{
  template: { key: string; name: string; description: string; colors: Record<string, string> };
  selected?: boolean;
}>();

defineEmits<{
  select: [key: string];
}>();

const bg = computed(() => props.template.colors.background || props.template.colors.primary);

const previewBg = computed(() => ({ background: bg.value }));

const headerBarBg = computed(() => ({
  background: props.template.colors.primary,
}));

const lineBg = computed(() => ({
  background: props.template.colors.text_light || "rgba(128,128,128,0.3)",
}));

const accentBg = computed(() => ({
  background: props.template.colors.accent,
}));

const paletteColors = computed(() => {
  const c = props.template.colors;
  return [c.primary, c.secondary, c.accent, c.background].filter(Boolean);
});
</script>

<style scoped>
.template-card {
  border-radius: var(--radius-lg);
  border: 2px solid var(--border);
  overflow: hidden;
  cursor: pointer;
  transition: all var(--transition-fast);
  background: var(--card);
  position: relative;
}
.template-card:hover {
  border-color: var(--primary-light);
  box-shadow: var(--shadow-lg);
  transform: translateY(-2px);
}
.template-card.selected {
  border-color: var(--primary);
  box-shadow: 0 0 0 3px rgba(79, 70, 229, 0.15);
}

.card-preview {
  aspect-ratio: 16 / 9;
  position: relative;
  overflow: hidden;
  padding: 14%;
  display: flex;
  flex-direction: column;
  gap: 10%;
}

.preview-header-bar {
  height: 16%;
  border-radius: 3px;
  opacity: 0.9;
}

.preview-body {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 8%;
  padding-top: 4%;
}

.preview-line {
  height: 7%;
  border-radius: 2px;
  opacity: 0.4;
}
.preview-line.w75 { width: 75%; }
.preview-line.w50 { width: 50%; }

.preview-accent {
  position: absolute;
  bottom: 10%;
  right: 10%;
  width: 18%;
  height: 14%;
  border-radius: 3px;
}

.card-body {
  padding: 10px 14px 14px;
}

.card-name {
  font-size: 14px;
  font-weight: 600;
  color: var(--text);
  margin-bottom: 3px;
}

.card-desc {
  font-size: 12px;
  color: var(--muted);
  line-height: 1.5;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  margin-bottom: 8px;
}

.card-colors {
  display: flex;
  gap: 5px;
}

.color-dot {
  width: 14px;
  height: 14px;
  border-radius: 50%;
  border: 1px solid var(--border);
}

.check-badge {
  position: absolute;
  top: 8px;
  right: 8px;
}
</style>
