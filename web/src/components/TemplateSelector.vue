<template>
  <div class="template-selector">
    <div class="selector-label">选择模板风格</div>
    <div class="template-row">
      <TemplateCard
        v-for="t in templates"
        :key="t.key"
        :template="t"
        :selected="selectedKey === t.key"
        @select="onSelect"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from "vue";
import client from "../api/client";
import TemplateCard from "./TemplateCard.vue";

const emit = defineEmits<{
  select: [key: string];
}>();

const templates = ref<any[]>([]);
const selectedKey = ref<string | null>(null);
const selecting = ref(false);

onMounted(async () => {
  try {
    const { data } = await client.get("/templates");
    templates.value = data.templates ?? [];
  } catch {
    // ignore
  }
});

function onSelect(key: string) {
  if (selecting.value) return;
  selecting.value = true;
  selectedKey.value = key;
  emit("select", key);
}
</script>

<style scoped>
.template-selector {
  padding: var(--space-md) var(--space-xl);
  background: var(--card);
  border-top: 1px solid var(--border);
}

.selector-label {
  font-size: 13px;
  font-weight: 600;
  color: var(--text);
  margin-bottom: var(--space-md);
}

.template-row {
  display: flex;
  gap: var(--space-md);
  overflow-x: auto;
  padding-bottom: var(--space-sm);
}
</style>
