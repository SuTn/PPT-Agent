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
      {{ uploading ? "上传中..." : "📎 上传文件" }}
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
  gap: 8px;
  padding: 6px 0;
}

.file-upload.dragging {
  background: var(--active);
  border-radius: 6px;
}

.btn-upload {
  padding: 4px 10px;
  border: 1px solid var(--border);
  background: transparent;
  border-radius: 6px;
  cursor: pointer;
  font-size: 12px;
  color: var(--muted);
}

.btn-upload:hover:not(:disabled) {
  border-color: var(--primary);
  color: var(--primary);
}

.btn-upload:disabled {
  opacity: 0.5;
}

.file-name {
  font-size: 12px;
  color: var(--muted);
}
</style>
