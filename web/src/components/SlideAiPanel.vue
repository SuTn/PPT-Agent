<template>
  <div class="ai-panel">
    <div class="ai-panel-header">
      <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
        <path d="M8 1l2 4.5H15l-3.8 3 1.4 4.5L8 10l-4.6 3 1.4-4.5L1 5.5h5L8 1z" stroke="currentColor" stroke-width="1.2" stroke-linejoin="round"/>
      </svg>
      <span>AI 编辑</span>
    </div>

    <div v-if="applied" class="ai-applied">
      <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
        <path d="M2 7l4 4 6-6" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
      </svg>
      <span>修改已预览，请使用工具栏保存或还原</span>
    </div>

    <div v-if="error" class="ai-error">{{ error }}</div>

    <div class="ai-input-area">
      <textarea
        v-model="instruction"
        class="ai-input"
        placeholder="描述你想要的修改，如：把标题改成 XXX、配色调亮一些…"
        rows="3"
        :disabled="loading"
        @keydown.enter.meta="submit"
        @keydown.enter.ctrl="submit"
      />
      <button class="ai-submit" :disabled="!instruction.trim() || loading" @click="submit">
        <span v-if="loading" class="spinner" />
        <template v-else>发送</template>
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from "vue";
import client from "../api/client";

const props = defineProps<{
  sessionId: string;
  filename: string;
}>();

const emit = defineEmits<{
  (e: "apply", html: string): void;
}>();

const instruction = ref("");
const loading = ref(false);
const error = ref<string | null>(null);
const applied = ref(false);

async function submit() {
  const text = instruction.value.trim();
  if (!text || loading.value) return;

  loading.value = true;
  error.value = null;
  applied.value = false;

  try {
    const { data } = await client.post(
      `/sessions/${props.sessionId}/slides/${props.filename}/ai-edit`,
      { instruction: text },
    );
    applied.value = true;
    emit("apply", data.html);
  } catch (err: any) {
    const msg = err?.response?.data?.detail || err?.message || "请求失败";
    error.value = msg;
  } finally {
    loading.value = false;
  }
}
</script>

<style scoped>
.ai-panel {
  width: 300px;
  flex-shrink: 0;
  border-left: 1px solid var(--border);
  background: var(--card);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.ai-panel-header {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  padding: var(--space-md) var(--space-lg);
  font-size: 13px;
  font-weight: 600;
  color: var(--text);
  border-bottom: 1px solid var(--border);
}

.ai-applied {
  display: flex;
  align-items: flex-start;
  gap: var(--space-sm);
  padding: var(--space-sm) var(--space-lg);
  font-size: 12px;
  color: #065f46;
  background: #ecfdf5;
  border-bottom: 1px solid #a7f3d0;
  line-height: 1.5;
}

.ai-applied svg {
  flex-shrink: 0;
  margin-top: 2px;
}

.ai-error {
  padding: var(--space-sm) var(--space-lg);
  font-size: 12px;
  color: #991b1b;
  background: #fef2f2;
  border-bottom: 1px solid #fecaca;
  line-height: 1.5;
}

.ai-input-area {
  flex: 1;
  display: flex;
  flex-direction: column;
  padding: var(--space-md) var(--space-lg);
  gap: var(--space-sm);
}

.ai-input {
  flex: 1;
  resize: none;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  padding: var(--space-sm);
  font-size: 13px;
  line-height: 1.5;
  color: var(--text);
  background: var(--bg);
  font-family: inherit;
  min-height: 80px;
}

.ai-input:focus {
  outline: none;
  border-color: var(--primary-light);
  box-shadow: 0 0 0 2px rgba(79, 70, 229, 0.1);
}

.ai-input::placeholder {
  color: var(--muted);
}

.ai-submit {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 32px;
  border: none;
  border-radius: var(--radius-sm);
  background: var(--primary);
  color: white;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: background var(--transition-fast);
}

.ai-submit:hover:not(:disabled) {
  background: var(--primary-dark);
}

.ai-submit:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.spinner {
  display: inline-block;
  width: 14px;
  height: 14px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-top-color: white;
  border-radius: 50%;
  animation: spin 0.6s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}
</style>
