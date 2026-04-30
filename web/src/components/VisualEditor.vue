<template>
  <div class="visual-editor">
    <iframe
      ref="iframeRef"
      class="visual-iframe"
      sandbox="allow-same-origin"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, watch, onUnmounted } from "vue";

const EDITABLE_SELECTORS = [
  "h1", "h2", "h3", "h4", "h5", "h6",
  "p", "li", "span", "a", "strong", "em",
  "td", "th", "figcaption", "blockquote",
].join(", ");

const EDIT_STYLE_ID = "ppt-agent-edit-styles";

const props = defineProps<{ html: string }>();
const emit = defineEmits<{ (e: "update", html: string): void }>();

const iframeRef = ref<HTMLIFrameElement | null>(null);
let observer: MutationObserver | null = null;
let debounceTimer: ReturnType<typeof setTimeout> | null = null;

function clearDebounce() {
  if (debounceTimer) {
    clearTimeout(debounceTimer);
    debounceTimer = null;
  }
}

function onMutate() {
  clearDebounce();
  debounceTimer = setTimeout(() => {
    const doc = iframeRef.value?.contentDocument;
    if (doc) {
      emit("update", serializeHtml(doc));
    }
  }, 300);
}

function injectEditStyles(doc: Document) {
  if (doc.getElementById(EDIT_STYLE_ID)) return;
  const style = doc.createElement("style");
  style.id = EDIT_STYLE_ID;
  style.textContent = `
    [contenteditable="true"] {
      outline: 2px dashed rgba(79,70,229,0.35);
      outline-offset: 2px;
      min-height: 1em;
      cursor: text;
    }
    [contenteditable="true"]:hover {
      outline-color: rgba(79,70,229,0.6);
    }
    [contenteditable="true"]:focus {
      outline: 2px solid rgba(79,70,229,0.8);
      background: rgba(79,70,229,0.04);
    }
  `;
  doc.head.appendChild(style);
}

function enableContentEditable(doc: Document) {
  doc.querySelectorAll(EDITABLE_SELECTORS).forEach((el) => {
    const hasText = Array.from(el.childNodes).some(
      (n) => n.nodeType === Node.TEXT_NODE && (n.textContent?.trim().length ?? 0) > 0,
    );
    if (hasText) {
      (el as HTMLElement).contentEditable = "true";
    }
  });
}

function startObserver(doc: Document) {
  stopObserver();
  observer = new MutationObserver(onMutate);
  observer.observe(doc.body, {
    characterData: true,
    childList: true,
    subtree: true,
  });
}

function stopObserver() {
  if (observer) {
    observer.disconnect();
    observer = null;
  }
}

function setupIframe() {
  const iframe = iframeRef.value;
  if (!iframe) return;

  iframe.srcdoc = props.html;

  iframe.onload = () => {
    const doc = iframe.contentDocument;
    if (!doc) return;
    injectEditStyles(doc);
    enableContentEditable(doc);
    startObserver(doc);
  };
}

function serializeHtml(doc: Document): string {
  // Clone to avoid modifying the live DOM
  const clone = doc.documentElement.cloneNode(true) as HTMLElement;

  // Remove injected edit styles
  const editStyle = clone.querySelector(`#${EDIT_STYLE_ID}`);
  if (editStyle) editStyle.remove();

  // Remove contenteditable and browser-injected attributes
  clone.querySelectorAll("[contenteditable]").forEach((el) => {
    el.removeAttribute("contenteditable");
  });
  clone.querySelectorAll("[spellcheck]").forEach((el) => {
    el.removeAttribute("spellcheck");
  });

  return "<!DOCTYPE html>\n" + clone.outerHTML;
}

// Public method for parent to get cleaned HTML
function getCleanedHtml(): string {
  const doc = iframeRef.value?.contentDocument;
  if (!doc) return props.html;
  return serializeHtml(doc);
}

watch(() => props.html, setupIframe);

onUnmounted(() => {
  stopObserver();
  clearDebounce();
});

defineExpose({ getCleanedHtml });
</script>

<style scoped>
.visual-editor {
  display: flex;
  align-items: center;
  justify-content: center;
  flex: 1;
  overflow: hidden;
  background: var(--bg);
}
.visual-iframe {
  width: 1280px;
  height: 720px;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  transform-origin: center center;
}
</style>
