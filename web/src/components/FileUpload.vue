<template>
  <div
    class="file-upload"
    :class="{ dragging: isDragging }"
    @dragover.prevent="isDragging = true"
    @dragleave="isDragging = false"
    @drop.prevent="handleDrop"
  >
    <input
      ref="fileInput"
      type="file"
      style="display: none"
      @change="handleSelect"
    />
    <button type="button" class="btn-upload" @click="fileInput?.click()" :disabled="uploading">
      <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
        <path d="M7 2v6M4.5 5L7 2 9.5 5M2 9v2a1 1 0 001 1h8a1 1 0 001-1V9" stroke="currentColor" stroke-width="1.3" stroke-linecap="round" stroke-linejoin="round"/>
      </svg>
      {{ uploading ? "上传中..." : "上传" }}
    </button>
    <span v-if="fileName" class="file-name">{{ fileName }}</span>
  </div>
</template>

<script setup lang="ts">
import { ref } from "vue";
import client from "../api/client";

const props = defineProps<{ sessionId: string }>();
const emit = defineEmits<{ uploaded: [result: string] }>();

const fileInput = ref<HTMLInputElement | null>(null);
const fileName = ref("");
const uploading = ref(false);
const isDragging = ref(false);

async function uploadFile(file: File) {
  if (uploading.value) return;
  uploading.value = true;
  fileName.value = file.name;

  try {
    const formData = new FormData();
    formData.append("file", file);
    const { data } = await client.post(`/sessions/${props.sessionId}/upload`, formData);
    emit("uploaded", data.result);
  } catch {
    emit("uploaded", "文件上传失败");
  } finally {
    uploading.value = false;
  }
}

function handleSelect(e: Event) {
  const file = (e.target as HTMLInputElement).files?.[0];
  if (file) uploadFile(file);
  if (fileInput.value) fileInput.value.value = "";
}

function handleDrop(e: DragEvent) {
  isDragging.value = false;
  const file = e.dataTransfer?.files[0];
  if (file) uploadFile(file);
}
</script>

<style scoped>
.file-upload {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  padding: var(--space-sm) var(--space-xl) 0;
}

.file-upload.dragging {
  background: var(--info-light);
  border-radius: var(--radius-md);
}

.btn-upload {
  display: inline-flex;
  align-items: center;
  gap: var(--space-xs);
  padding: 4px 10px;
  border: 1px solid var(--border);
  background: transparent;
  border-radius: var(--radius-sm);
  cursor: pointer;
  font-size: 12px;
  color: var(--muted);
  transition: all var(--transition-fast);
}
.btn-upload:hover:not(:disabled) {
  border-color: var(--primary-light);
  color: var(--primary);
}
.btn-upload:disabled {
  opacity: 0.5;
}

.file-name {
  font-size: 12px;
  color: var(--muted);
  max-width: 200px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
</style>
