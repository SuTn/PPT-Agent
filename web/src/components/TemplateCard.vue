<template>
  <div class="template-card" :class="{ selected }" @click="$emit('select', template.key)">
    <div class="color-bar" :style="gradientStyle"></div>
    <div class="card-body">
      <div class="card-name">{{ template.name }}</div>
      <div class="card-desc">{{ template.description }}</div>
    </div>
    <div v-if="selected" class="check">
      <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
        <path d="M2 6l3 3 5-5" stroke="white" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
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

const gradientStyle = computed(() => ({
  background: `linear-gradient(135deg, ${props.template.colors.primary}, ${props.template.colors.accent})`,
}));
</script>

<style scoped>
.template-card {
  width: 160px;
  border-radius: var(--radius-md);
  border: 2px solid var(--border);
  overflow: hidden;
  cursor: pointer;
  transition: all var(--transition-fast);
  background: var(--card);
  flex-shrink: 0;
  position: relative;
}
.template-card:hover {
  border-color: var(--primary-light);
  box-shadow: var(--shadow-md);
  transform: translateY(-2px);
}
.template-card.selected {
  border-color: var(--primary);
  box-shadow: 0 0 0 2px rgba(79, 70, 229, 0.2);
}

.color-bar {
  height: 48px;
}

.card-body {
  padding: var(--space-md);
}

.card-name {
  font-size: 13px;
  font-weight: 600;
  color: var(--text);
  margin-bottom: 2px;
}

.card-desc {
  font-size: 11px;
  color: var(--muted);
  line-height: 1.4;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.check {
  position: absolute;
  top: var(--space-sm);
  right: var(--space-sm);
  width: 20px;
  height: 20px;
  background: var(--primary);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
}
</style>
