<template>
  <form class="input-bar" @submit.prevent="handleSubmit">
    <div class="input-wrapper" :class="{ focused }">
      <div class="mode-toggle">
        <button type="button" class="mode-btn" :class="{ active: mode === 'fast' }" @click="$emit('update:mode', 'fast')" title="快速模式：自动完成所有步骤">快速</button>
        <button type="button" class="mode-btn" :class="{ active: mode === 'standard' }" @click="$emit('update:mode', 'standard')" title="标准模式：逐步确认大纲和模板">标准</button>
      </div>
      <textarea
        v-model="text"
        @keydown.enter.exact.prevent="handleSubmit"
        @focus="focused = true"
        @blur="focused = false"
        @input="autoResize"
        ref="textareaRef"
        rows="1"
        :placeholder="disabled ? '处理中...' : '输入你的需求...'"
        :disabled="disabled"
      ></textarea>
      <button type="submit" class="send-btn" :disabled="!text.trim() || disabled">
        <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
          <path d="M3 9h12M10 4l5 5-5 5" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
      </button>
    </div>
  </form>
</template>

<script setup lang="ts">
import { ref, nextTick } from "vue";

const props = defineProps<{
  disabled?: boolean;
  mode?: "fast" | "standard";
}>();

const emit = defineEmits<{
  send: [content: string];
  "update:mode": [mode: "fast" | "standard"];
}>();

const text = ref("");
const focused = ref(false);
const textareaRef = ref<HTMLTextAreaElement | null>(null);

function handleSubmit() {
  const trimmed = text.value.trim();
  if (!trimmed || props.disabled) return;
  emit("send", trimmed);
  text.value = "";
  nextTick(() => {
    if (textareaRef.value) {
      textareaRef.value.style.height = "auto";
    }
  });
}

function autoResize() {
  const el = textareaRef.value;
  if (!el) return;
  el.style.height = "auto";
  el.style.height = Math.min(el.scrollHeight, 120) + "px";
}
</script>

<style scoped>
.input-bar {
  padding: var(--space-md) var(--space-xl);
}

.input-wrapper {
  display: flex;
  align-items: flex-end;
  gap: var(--space-sm);
  background: var(--card);
  border: 2px solid var(--border);
  border-radius: var(--radius-lg);
  padding: var(--space-sm) var(--space-sm) var(--space-sm) var(--space-md);
  transition: border-color var(--transition-fast), box-shadow var(--transition-fast);
}

.input-wrapper.focused {
  border-color: var(--primary-light);
  box-shadow: 0 0 0 3px rgba(79, 70, 229, 0.1);
}

.mode-toggle {
  display: flex;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  overflow: hidden;
  flex-shrink: 0;
  align-self: center;
}

.mode-btn {
  padding: 3px 8px;
  border: none;
  background: transparent;
  color: var(--muted);
  font-size: 11px;
  font-weight: 600;
  cursor: pointer;
  transition: all var(--transition-fast);
  white-space: nowrap;
}
.mode-btn:hover {
  color: var(--text-secondary);
}
.mode-btn.active {
  background: var(--primary);
  color: white;
}

textarea {
  flex: 1;
  border: none;
  outline: none;
  resize: none;
  font-size: 14px;
  line-height: 1.5;
  font-family: var(--font-sans);
  color: var(--text);
  background: transparent;
  max-height: 120px;
  padding: var(--space-xs) 0;
}
textarea::placeholder {
  color: var(--muted);
}
textarea:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.send-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  border: none;
  border-radius: var(--radius-md);
  background: var(--primary);
  color: white;
  cursor: pointer;
  flex-shrink: 0;
  transition: all var(--transition-fast);
}
.send-btn:hover:not(:disabled) {
  background: var(--primary-dark);
}
.send-btn:disabled {
  background: var(--border);
  color: var(--muted);
  cursor: not-allowed;
}
</style>
