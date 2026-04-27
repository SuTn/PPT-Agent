<template>
  <form class="input-bar" @submit.prevent="handleSend">
    <textarea
      v-model="text"
      placeholder="输入你的需求..."
      :disabled="disabled"
      rows="1"
      @keydown.enter.exact.prevent="handleSend"
      @input="autoResize"
    ></textarea>
    <button type="submit" :disabled="disabled || !text.trim()">
      发送
    </button>
  </form>
</template>

<script setup lang="ts">
import { ref } from "vue";

defineProps<{ disabled: boolean }>();
const emit = defineEmits<{ send: [content: string] }>();

const text = ref("");

function handleSend() {
  const content = text.value.trim();
  if (!content) return;
  emit("send", content);
  text.value = "";
}

function autoResize(e: Event) {
  const el = e.target as HTMLTextAreaElement;
  el.style.height = "auto";
  el.style.height = Math.min(el.scrollHeight, 120) + "px";
}
</script>

<style scoped>
.input-bar {
  display: flex;
  gap: 8px;
  align-items: flex-end;
}

textarea {
  flex: 1;
  padding: 10px 14px;
  border: 1px solid var(--border);
  border-radius: 8px;
  font-size: 14px;
  line-height: 1.5;
  resize: none;
  outline: none;
  font-family: inherit;
}

textarea:focus {
  border-color: var(--primary);
}

textarea:disabled {
  opacity: 0.5;
}

button {
  padding: 10px 20px;
  background: var(--primary);
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  cursor: pointer;
  white-space: nowrap;
}

button:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

button:not(:disabled):hover {
  opacity: 0.9;
}
</style>
