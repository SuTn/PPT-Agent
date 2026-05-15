<template>
  <div class="stepper">
    <div v-for="(step, i) in steps" :key="step.key" class="step">
      <div class="step-node" :class="nodeClass(step.key)">
        <svg v-if="isCompleted(step.key)" width="12" height="12" viewBox="0 0 12 12" fill="none">
          <path d="M2 6l3 3 5-5" stroke="white" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
        <span v-else-if="isCurrent(step.key)" class="step-pulse"></span>
        <span v-else class="step-dot-inner"></span>
      </div>
      <span class="step-label" :class="{ active: isCurrent(step.key) }">{{ step.label }}</span>
      <span
        v-if="step.key === 'template_done' && isCompleted(step.key) && template"
        class="step-template-tag"
        @click="$emit('changeTemplate')"
      >
        <span class="tag-dot" :style="{ background: template.colors.primary }"></span>
        {{ template.name }}
        <svg width="10" height="10" viewBox="0 0 10 10" fill="none">
          <path d="M7.5 2l.5.5-6 6H1.5v-.5l6-6z" stroke="currentColor" stroke-width="0.8" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
      </span>
      <div v-if="i < steps.length - 1" class="step-line" :class="{ filled: isCompleted(step.key) }"></div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue";

const props = defineProps<{
  currentStep: string;
  template?: { key: string; name: string; description: string; colors: Record<string, string> } | null;
}>();

defineEmits<{
  changeTemplate: [];
}>();

const STEP_ORDER = ["idle", "template_done", "research_done", "outline_done", "slides_done", "exported"];

const steps = [
  { key: "idle", label: "开始" },
  { key: "template_done", label: "模板" },
  { key: "research_done", label: "研究" },
  { key: "outline_done", label: "大纲" },
  { key: "slides_done", label: "幻灯片" },
  { key: "exported", label: "导出" },
];

// Map generating_slides → slides_done so stepper shows "幻灯片" as current
const effectiveStep = computed(() =>
  props.currentStep === "generating_slides" ? "slides_done" : props.currentStep
);

function stepIndex(key: string): number {
  return STEP_ORDER.indexOf(key);
}

function isCompleted(key: string): boolean {
  return stepIndex(key) < stepIndex(effectiveStep.value);
}

function isCurrent(key: string): boolean {
  return stepIndex(key) === stepIndex(effectiveStep.value);
}

function nodeClass(key: string): string {
  if (isCompleted(key)) return "node-completed";
  if (isCurrent(key)) return "node-current";
  return "node-pending";
}
</script>

<style scoped>
.stepper {
  display: flex;
  align-items: center;
  gap: 0;
  padding: var(--space-sm) var(--space-xl);
}

.step {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
}

.step-node {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  position: relative;
}

.node-completed {
  background: var(--primary);
}

.node-current {
  background: var(--primary);
  box-shadow: 0 0 0 3px rgba(79, 70, 229, 0.2);
}

.node-pending {
  background: var(--border);
}

.step-pulse {
  width: 8px;
  height: 8px;
  background: white;
  border-radius: 50%;
  animation: pulse-dot 1.5s ease-in-out infinite;
}

.step-dot-inner {
  width: 8px;
  height: 8px;
  background: var(--muted);
  border-radius: 50%;
}

@keyframes pulse-dot {
  0%, 100% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.6; transform: scale(0.7); }
}

.step-label {
  font-size: 11px;
  color: var(--muted);
  white-space: nowrap;
}
.step-label.active {
  color: var(--primary);
  font-weight: 600;
}

.step-template-tag {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 2px 8px;
  background: var(--bg);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  font-size: 11px;
  color: var(--text-secondary);
  cursor: pointer;
  transition: all var(--transition-fast);
  white-space: nowrap;
}
.step-template-tag:hover {
  border-color: var(--primary-light);
  color: var(--primary);
}

.tag-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}

.step-line {
  width: 24px;
  height: 2px;
  background: var(--border);
  margin: 0 var(--space-xs);
  border-radius: 1px;
}
.step-line.filled {
  background: var(--primary);
}
</style>
