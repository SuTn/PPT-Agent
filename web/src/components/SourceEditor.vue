<template>
  <div class="source-editor">
    <div class="source-pane">
      <div class="pane-header">HTML 源码</div>
      <textarea
        ref="textareaRef"
        class="source-textarea"
        :value="html"
        @input="onInput"
        @keydown="onKeydown"
        spellcheck="false"
      />
    </div>
    <div class="divider" />
    <div class="preview-pane">
      <div class="pane-header">预览</div>
      <div class="preview-container">
        <iframe
          ref="previewRef"
          class="preview-iframe"
          sandbox="allow-same-origin"
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, onUnmounted } from "vue";

const props = defineProps<{ html: string }>();
const emit = defineEmits<{ (e: "update", html: string): void }>();

const textareaRef = ref<HTMLTextAreaElement | null>(null);
const previewRef = ref<HTMLIFrameElement | null>(null);
let debounceTimer: ReturnType<typeof setTimeout> | null = null;

function clearDebounce() {
  if (debounceTimer) {
    clearTimeout(debounceTimer);
    debounceTimer = null;
  }
}

function updatePreview(html: string) {
  const iframe = previewRef.value;
  if (iframe) {
    iframe.srcdoc = html;
  }
}

function onInput() {
  const textarea = textareaRef.value;
  if (!textarea) return;
  const val = textarea.value;
  clearDebounce();
  debounceTimer = setTimeout(() => {
    emit("update", val);
    updatePreview(val);
  }, 500);
}

function onKeydown(e: KeyboardEvent) {
  if (e.key === "Tab") {
    e.preventDefault();
    const textarea = textareaRef.value!;
    const start = textarea.selectionStart;
    const end = textarea.selectionEnd;
    textarea.value = textarea.value.substring(0, start) + "  " + textarea.value.substring(end);
    textarea.selectionStart = textarea.selectionEnd = start + 2;
    onInput();
  }
}

watch(
  () => props.html,
  (newHtml) => {
    updatePreview(newHtml);
  },
);

onUnmounted(() => {
  clearDebounce();
});
</script>

<style scoped>
.source-editor {
  display: flex;
  flex: 1;
  overflow: hidden;
}
.source-pane,
.preview-pane {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}
.pane-header {
  padding: 6px 12px;
  font-size: 12px;
  font-weight: 600;
  color: var(--text-secondary);
  background: var(--card);
  border-bottom: 1px solid var(--border);
  user-select: none;
}
.source-textarea {
  flex: 1;
  resize: none;
  border: none;
  outline: none;
  padding: 12px;
  font-family: "Menlo", "Consolas", "Monaco", monospace;
  font-size: 13px;
  line-height: 1.6;
  color: var(--text);
  background: var(--card);
  tab-size: 2;
}
.divider {
  width: 1px;
  background: var(--border);
}
.preview-container {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--bg);
  overflow: hidden;
}
.preview-iframe {
  width: 1280px;
  height: 720px;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  transform-origin: center center;
}
</style>
