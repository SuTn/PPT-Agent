<template>
  <div class="template-selector">
    <div class="selector-header">
      <div class="selector-title">选择模板风格</div>
      <div class="selector-subtitle">选择一个适合你演示场景的模板</div>
    </div>
    <div class="template-grid">
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
  select: [template: { key: string; name: string; description: string; colors: Record<string, string> }];
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
  const t = templates.value.find((t) => t.key === key);
  if (t) emit("select", t);
}
</script>

<style scoped>
.template-selector {
  width: 100%;
  max-width: 860px;
  padding: var(--space-2xl);
  background: var(--card);
  border-radius: var(--radius-xl);
  box-shadow: var(--shadow-md);
}

.selector-header {
  margin-bottom: var(--space-lg);
}

.selector-title {
  font-size: 16px;
  font-weight: 700;
  color: var(--text);
  margin-bottom: 2px;
}

.selector-subtitle {
  font-size: 13px;
  color: var(--muted);
}

.template-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: var(--space-md);
}
</style>
